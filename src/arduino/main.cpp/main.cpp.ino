
#include <Wire.h>
// Ambient light sensor
#include "DFRobot_VEML7700.h"

// Digital pin id-s.
const int cDropFlowMeterId = 3;
const int cPumpRelayId = 8;
const int cValveRelayId = 7;
const int cSolarRelayId = 4;
const int cGeneratorRelayId = 2;

//! Total number of used analog pins
const int cAnalogCount = 4;
// Analog pins
const int cUpperTankWeightSensorId = A0;
const int cLowerTankWeightSensorId = A1;
const int cCurrentSensorId = A2;
const int cBatteryVoltageSensorId = A4;


// Flow meter consts. To represent 1 liter of flow the number of squarewaves below shall happen.
const int cDropFlow_WavePerLiter = 450;
const int cLiftFlow_WavePerLiter = 5880;

//! Control state descriptor.
struct ControlState
{
    int isManual;
    int bottomTankEmptyCounter;
    int topTankEmptyCounter;
    int requestedPumpState;
    int pumpState;
    int requestedValveState;
    int valveState;
    int requestedSolarState;
    int solarState;
    int requestedGeneratorState;
    int generatorState;
    int isLowVoltageShutdown;
};
ControlState gControl;
const int cRelayStateOn = 1;
const int cRelayStateOff = 0;


// Ambient light sensor constants
const int cDaylight_lux = 100;

// Voltage and current conversion constants
const float c5VConversion = 1.0;
const float cVRef_mV = 510.0;
const float cVSensitivity_mVperA = 11.0; // 136 mV/A resolution
const float cVBatLow_mV = 3100.0;
const float cVBatOk_mV = 3900.0;

// Moving average control
const int cAvgSampleCount = 1;
int gSampleCounter = 0;
float gAnalogSamples[cAnalogCount][cAvgSampleCount];
float gSampleAccum[cAnalogCount];
bool gAvgBufferSaturated = false;

// Networking
unsigned long gWatchdogCount = 0;
bool ledON = false;

struct Measurements
{
  float ambientLight_lux{0.0};
  float dropFlow_lpmin{0.0};
  float upperTankLevel_l{0.0};
  float lowerTankLevel_l{0.0};
  float current_mA{0.0};
  float batteryVoltage_mV{0.0};
};

// An interesting observation
// Sometimes I received the following message. with DF Robot WifiBee module.
// 20:47:58.744 -> DNS wiki.dfrobot.com.cn, 111.231.115.214 log come up, shady???
// I believe, that when someone buys a module, whuch purpose is to provide a wifi interface
// I shouldn't be seeing any DNS identification towards the manufacturer.
const char ssid[]={
  "AT+SSID=Hogspot2G"};   // WiFi SSID
const char passwd[]={
  "AT+PASSWORD=mortythebooty007"}; // WiFi  password

DFRobot_VEML7700 als;

/*! Initializes the WifiBee-MT7681 module
 *  Only need to run once to configure the module
 */
void initWifi()
{
  while(!Serial);
  Serial.print("+++");
  delay(1000);
  Serial.println(ssid);
  delay(100);
  Serial.println(passwd);
  delay(100);
  Serial.println("AT+HOSTNAME=?");
  delay(100);
  Serial.println("AT+REBOOT");
  delay(100);
  Serial.println("AT+CONNECT");
  delay(10000);
}

//! Setup arduino control
void setup() {
  // Configure PWM frequency.
  //TCCR0B = 0b00000001; // x1
  //TCCR0A = 0b00000011; // fast pwm
  //TCCR0B = 0b00000010; // x8
  //TCCR0A = 0b00000011; // fast pwm
  
  Serial.begin(115200);

  // Configure digital inputs, outputs.
  pinMode(cDropFlowMeterId, INPUT);
  pinMode(cPumpRelayId, OUTPUT);
  pinMode(cValveRelayId, OUTPUT);
  pinMode(cSolarRelayId, OUTPUT);
  pinMode(cGeneratorRelayId, OUTPUT);
  digitalWrite(cPumpRelayId, 0);
  digitalWrite(cValveRelayId, 0);
  digitalWrite(cSolarRelayId, 0);
  digitalWrite(cGeneratorRelayId, 0);

  // Initialize current sample averager buffer.
  for (int i = 0; i < cAnalogCount; i++)
  {
    gSampleAccum[i] = 0.0;
    for (int j = 0; j < cAvgSampleCount; j++)
    {
      gAnalogSamples[i][j] = 0.0;
    }
  }
  delay(100);

  // Setup control variables.
  gControl.bottomTankEmptyCounter = 0;
  gControl.topTankEmptyCounter = 0;
  gControl.pumpState = 0;
  gControl.requestedPumpState = 0;
  gControl.valveState = 0;
  gControl.requestedValveState = 0;
  gControl.generatorState = 0;
  gControl.requestedGeneratorState = 0;
  gControl.solarState = 0;
  gControl.requestedSolarState = 0;
  gControl.isManual = 1;
  gControl.isLowVoltageShutdown = 0;

  // Using the serial as it seemed to be faster than using DF Robot WifiBee module.
  //initWifi();
  
  pinMode(LED_BUILTIN, OUTPUT);

  // Initialize ambient light sensor interface.
  als.begin();
}

//! Returns the lightintensity measured by the ambient light sensor.
float GetLightIntensity_lux()
{
    float lux;
    als.getALSLux(lux);
    return lux;
}

/*! Returns the flow in liter per minutes for the given sensor. In the current sensors x number of squarewaves represent a liter.
 *  \param[in] flowMeterId  id of the sensor pin
 *  \param[in] flowConst_WavePerLiter sensor squarewave count representing 1 liter flow.
 *  
 *  \return The flow in l/min unit.
 */
float GetFlow_lpmin(int flowMeterId, int flowConst_WavePerLiter)
{
  int ontime, offtime;
  float freq, period;
  ontime = abs(pulseIn(flowMeterId, HIGH));
  offtime = abs(pulseIn(flowMeterId, LOW));
  period = ontime + offtime;
  if (period != 0)
    freq = 1000000.0 / period;
  else
    freq = 0;
  return -freq * 60 / flowConst_WavePerLiter;
}

/*! Sensor ids are not starting from 0 and are not continuous
 *  This function will return id-s that meet the above two conditions.
 */
int ConvertSensorIdToSampleContainerId(int sensorId)
{
  switch(sensorId)
  {
      case cUpperTankWeightSensorId:
          return 0;
      case cLowerTankWeightSensorId:
          return 1;
      case cCurrentSensorId:
          return 2;
      case cBatteryVoltageSensorId:
          return 3;
      default:
          return 0;
  }
}

/*! Updates averager control parameters.
 */
void UpdateAverager()
{
    gSampleCounter++;
    if (gSampleCounter == cAvgSampleCount)
    {
        gSampleCounter = 0;
        gAvgBufferSaturated = true;
    }  
}

/*! Stores, calculates and returns the moving average of a sensor measurement
 *  \param[in] sensorId id of the sensor.
 *  \param[in] sample The new sample to process.
 *  
 *  \return Average value of the measurement.
*/
float GetAvgSample(int sensorId, float sample)
{
    int sampleContainerId = ConvertSensorIdToSampleContainerId(sensorId);
    if (gAvgBufferSaturated)
        gSampleAccum[sampleContainerId] -= gAnalogSamples[sampleContainerId][gSampleCounter]; 
    gAnalogSamples[sampleContainerId][gSampleCounter] = sample;
    gSampleAccum[sampleContainerId] += sample;
    return gSampleAccum[sampleContainerId] / cAvgSampleCount; 
}

/*! Returns the moving average current samples for the give sensor.
 *  \param[in] sensorId id of the current sensor pin
 *  
 *  \return the averaged current in mA.
 */
float GetAvgCurrent_mA(int sensorId)
{
    float rawCurrent_mV = analogRead(sensorId);
    //float rawCurrent_mV = -2.75 * analogRead(sensorId) + 1740.0;
    rawCurrent_mV = (rawCurrent_mV - cVRef_mV) * cVSensitivity_mVperA ;
    return GetAvgSample(sensorId, rawCurrent_mV);
}

/*! Returns the tank level of the selected tank in liters.
 *  The magic numbers are set based on empirical measurements. 
 *  The force sense resistor is not providing linear behaviour at this weight range,
 *  so I had to play around until I got the output value roughly corresponding to the reality.
 *  Need to adjust everytime the setup is being moved.
 *  \param[in] tankId The id of the selected tank (top, bottom tank)
 *  
 *  \return the average tank level in liters.
*/
float GetTankLevel_l(int tankId)
{
    float data = 0.0;
    if (tankId == cLowerTankWeightSensorId)
      data = 0.0225*(analogRead(tankId)- 352);
    else
      data = 0.0225*(analogRead(tankId)- 460);
    // the measurement is a bit inaccurate, so every negative value is just truncated to zero.
    return GetAvgSample(tankId, data <= 0.0 ? 0.0 : data);
}

float GetBatteryVoltage_mV()
{
    float batteryVoltage_mV = analogRead(cBatteryVoltageSensorId) * c5VConversion;
    return GetAvgSample(cBatteryVoltageSensorId, batteryVoltage_mV);
}

void CheckWatchdog()
{
    if (gWatchdogCount > 4000)
    {
      gWatchdogCount = 0;
      Serial.write("$ARDY,*");
      if (ledON)
      {
        digitalWrite(LED_BUILTIN, HIGH);
        ledON = false;
      }
      else
      {
        digitalWrite(LED_BUILTIN, LOW);
        ledON = true;
      }
    }
    gWatchdogCount++;
}


//! Sends control states to the desktop client.
void SendControlFeedback()
{
    String resp = "$ACTL,";
    resp.concat(gControl.isManual);
    resp.concat(",");
    resp.concat(gControl.bottomTankEmptyCounter);
    resp.concat(",");
    resp.concat(gControl.topTankEmptyCounter);
    resp.concat(",");
    resp.concat(gControl.pumpState);
    resp.concat(",");
    resp.concat(gControl.valveState);
    resp.concat(",");
    resp.concat(gControl.solarState);
    resp.concat(",");
    resp.concat(gControl.generatorState);
    resp.concat(",");
    resp.concat(gControl.isLowVoltageShutdown);
    resp.concat("*");
    Serial.write(resp.c_str());
}

/*! Processes incoming messages, and generates responses using measurement data.
    Most of the messages just sending an ACK feedback except the RDTA, data message.
*/
void ProcessMessage(String msg, const Measurements& data)
{
  String header = msg.substring(0,5);
  if (header == "$RDTA")
  {
      gWatchdogCount = 0;
      String resp = "$ADTA,";
      resp.concat(data.ambientLight_lux);
      resp.concat(",");
      resp.concat(data.current_mA);
      resp.concat(",");
      resp.concat(data.batteryVoltage_mV);
      resp.concat(",");
      resp.concat(data.dropFlow_lpmin);
      resp.concat(",");
      resp.concat(data.upperTankLevel_l);
      resp.concat(",");
      resp.concat(data.lowerTankLevel_l);
      resp.concat(",");
      resp.concat(data.lowerTankLevel_l + data.upperTankLevel_l);
      resp.concat("*");
      Serial.write(resp.c_str());
  }
  else if(header == "$RSTT")
  {
      SendControlFeedback();
  }
  else if(header == "$RPMP")
  { 
      gControl.requestedPumpState = msg.substring(6, 7).toInt();
      Serial.write("$APMP*");
  }
  else if(header == "$RVLV")
  { 
      gControl.requestedValveState = msg.substring(6, 7).toInt();
      Serial.write("$AVLV*");
  }
  else if(header == "$RSLR")
  { 
      gControl.requestedSolarState = msg.substring(6, 7).toInt();
      Serial.write("$ASLR*");
  }
  else if(header == "$RGNR")
  { 
      gControl.requestedGeneratorState = msg.substring(6, 7).toInt();
      Serial.write("$AGNR*");
  }
  else if(header == "$RMNL")
  {
      gControl.isManual = msg.substring(6, 7).toInt();
      Serial.write("$AMNL*");
  }
}

/*! Returns true if the ambient light sensor 
 *  detects the minimum charging light radiation.
 *  
 */
bool isDay(const Measurements& data)
{
  return data.ambientLight_lux > cDaylight_lux;
}

/*! Returns true if the battery voltage is getting 
 *  low and needs charging.
 */
bool isBatteryLow(const Measurements& data)
{
  return data.batteryVoltage_mV < cVBatLow_mV;
}

/*! Returns true if the battery has operational voltage.
 */
bool isBatteryOk(const Measurements& data)
{
  return data.batteryVoltage_mV > cVBatOk_mV;
}

/*! Returns true if the pump is on.
 */
bool isPumping()
{
  return gControl.pumpState == cRelayStateOn;
}

/*! Returns true if there is no fluid in the bottom tank.
 */
bool isPumped(const Measurements& data)
{
  return data.lowerTankLevel_l <= 0.0;
}

/*! Returns true if the valve is on.
 */
bool isFluidDischarging()
{
  return gControl.valveState == cRelayStateOn;
}

/*! Returns true if there is no fluid in the top tank.
 */
bool isFluidDischarged(const Measurements& data)
{
  return data.upperTankLevel_l <= 0.0;
}

/*! Sets the new state for the selected relay
 *  if different from the current one.
 */
void setState(int relayId, int newState)
{
    int *pCurrentState = nullptr;
    switch(relayId)
    {
        case cPumpRelayId:
            pCurrentState = &gControl.pumpState;
            break; 
        case cValveRelayId:
            pCurrentState = &gControl.valveState;
            break;
        case cSolarRelayId:
            pCurrentState = &gControl.solarState;
            break;
        case cGeneratorRelayId:
            pCurrentState = &gControl.generatorState;
            break;
        default:
            return;
    }
    if (newState != *pCurrentState)
    {
        *pCurrentState = newState;
        digitalWrite(relayId, *pCurrentState);
    }
}

/*! Runs manual control state machine.
 *  Pump must be switched off if there is nothing to pump
 *  Solar and generator cannot be on at the same time
 *  to avoid reverse currents for these sources.
 */
void manualControl(const Measurements& data)
{
    setState(cValveRelayId, gControl.requestedValveState);
    if(gControl.requestedValveState)
    {
      gControl.requestedGeneratorState = 1;
      gControl.requestedSolarState = 0;
    }

    if (isPumped(data))
        setState(cPumpRelayId, cRelayStateOff);
    else
        setState(cPumpRelayId, gControl.requestedPumpState);

    if (gControl.requestedSolarState)
    {
        gControl.requestedGeneratorState = 0;
        setState(cGeneratorRelayId, gControl.requestedGeneratorState);
        // wait time makes sure the generator is off.
        delay(100);
        setState(cSolarRelayId, cRelayStateOn);
    }
    else
    {
        setState(cSolarRelayId, cRelayStateOff);
    }

    if (gControl.requestedGeneratorState)
    {
        gControl.requestedSolarState = 0;
        setState(cSolarRelayId, gControl.requestedSolarState);
        // wait time makes sure the solar is off.
        delay(100);
        setState(cGeneratorRelayId, cRelayStateOn);
    }
    else
    {
        setState(cGeneratorRelayId, cRelayStateOff);
    }

    if(isBatteryLow(data) && isFluidDischarged(data))
    {
        gControl.isLowVoltageShutdown = 1;
    }
    else if(!isBatteryLow(data) || !isFluidDischarged(data))
    {
        gControl.isLowVoltageShutdown = 0;
    }
}

/*! Runs automatic control
 *  It pumps and solar charges during the day, and turbine charges during the night.
 *  Makes sure that solar and generator is not on at the same time
 *  to avoid reverse current to the sources.
 *  
 *  If the upper tank is empty and the battery is low 
 *  a low battery shutdown signal will be sent to the remote.
 *  
 *  If the battery charges to operational voltage during fluid discharge
 *  the emptying process will stop.
 */
void autoControl(const Measurements& data)
{
    if (isDay(data))
    {
        setState(cValveRelayId, cRelayStateOff);
        setState(cGeneratorRelayId, cRelayStateOff);
        // wait time makes sure the generator is off.
        delay(100);
        setState(cSolarRelayId, cRelayStateOn);
        
        if (isBatteryOk(data) && !isPumped(data))
            setState(cPumpRelayId, cRelayStateOn);
        else if(isPumped(data))
            setState(cPumpRelayId, cRelayStateOff);
    }
    else
    {
        setState(cPumpRelayId, cRelayStateOff);
        setState(cSolarRelayId, cRelayStateOff);
        // wait time makes sure the solar is off.
        delay(100);

        if (isBatteryLow(data) && !isFluidDischarged(data))
        {
            setState(cGeneratorRelayId, cRelayStateOn);
            // no need to wait for generator turn on
            // valve opens very slow.
            setState(cValveRelayId, cRelayStateOn);
        }
        else if(isFluidDischarged(data) ||
                (isBatteryOk(data) && isFluidDischarging()))
        {
            setState(cGeneratorRelayId, cRelayStateOff);
            setState(cValveRelayId, cRelayStateOff);
        }
        else if(isBatteryLow(data) && isFluidDischarged(data))
        {
            gControl.isLowVoltageShutdown = 1;
        }
        else if(!isBatteryLow(data))
        {
            gControl.isLowVoltageShutdown = 0;
        }
    }
}

void loop() {
    Measurements data;
    data.ambientLight_lux = GetLightIntensity_lux();
    data.current_mA = GetAvgCurrent_mA(cCurrentSensorId);
    data.batteryVoltage_mV = GetBatteryVoltage_mV();
    if(gControl.generatorState)
      data.dropFlow_lpmin = GetFlow_lpmin(cDropFlowMeterId, cDropFlow_WavePerLiter);
    data.upperTankLevel_l = GetTankLevel_l(cUpperTankWeightSensorId); 
    data.lowerTankLevel_l = GetTankLevel_l(cLowerTankWeightSensorId);
    if (gControl.isManual == 0)
        autoControl(data);
    else
        manualControl(data);
           
    while(Serial.available() != 0)
    {
      String recvRaw = Serial.readString();
      int asterixIndex = 0;
      while (asterixIndex != -1)
      {
          asterixIndex = recvRaw.indexOf("*");
          recvRaw = recvRaw.substring(0,asterixIndex);
          ProcessMessage(recvRaw, data);
      }  
    }
    CheckWatchdog();
    UpdateAverager();
}
