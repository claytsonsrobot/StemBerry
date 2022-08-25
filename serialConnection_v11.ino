/*
 * Version Author: Clayton Bennett
 * Original Author: Austin Bebee
 * Version: 11
 * Last edited: August 24, 2022
 */
#include "Arduino.h"
#include <HX711.h>
#include <digitalWriteFast.h>

#define baudrate 115200 // 9600
#define wheelDiameter (32.35/359) //inches, yet wrong
#define kg_lbs 2.20462262 //kg to lbs
#define kg_Newtons 9.81 //kg to Newtons

//Bennett-era pin values, altered May 8, 2022
#define c_EncoderInterrupt 0 // not used
#define c_EncoderPinA 8
#define c_EncoderPinB   10
#define DOUT 7
#define CLK 6

String sentByte;
int rec;
int n = 0;
int incomingbyte;
long value_encoderTicks;
long value_encoderDegrees;
volatile bool _EncoderBSet;
volatile long _EncoderTicks = 0;
bool started = false;
bool stopped = false;
bool reset = true;
bool op = false;
char rbytes[1];
String caliStr;
float calibra = -199750; // calibration factor: working well, but user can update in RPi GUI
bool caliLoop = false;
bool showF = false;
float actualDiameter;
float failedNewtons = 0.000;
float Newtons;
float kgs;
uint32_t time_started_arduino;
uint32_t time_elapsed_arduino;
uint32_t timestamp_now; // = now.unixtime());


HX711 scale; //HX711 scale(DOUT, CLK); // NOTE: HX711 library was updated, if using newer version change to: HX711 scale;

void setup(){
    Serial.begin(baudrate);
    scale.begin(DOUT,CLK);
    scale.set_scale(); //here is the problem
    scale.tare(); //Reset the scale to 0
    long zero_factor = scale.read_average(); 
    // Left encoder
    pinMode(c_EncoderPinA, INPUT);      // sets pin A as input
    digitalWrite(c_EncoderPinA, LOW);  // turn on pullup resistors
    pinMode(c_EncoderPinB, INPUT);      // sets pin B as input
    digitalWrite(c_EncoderPinB, LOW);  // turn on pullup resistors
    attachInterrupt(c_EncoderInterrupt, rotation, RISING);  
}
void loop() {
    delay(.5); // delay needed?      
    if (Serial.available() > 0){ // data recieved!
            rbytes[n] = Serial.read(); // read data
            incomingbyte = rbytes[n];
            if(rbytes[n] == 's'){//DATA COLLECTION BEGINS
                    if(started == false){
                            Serial.println("Started!"); //Serial.println(sentByte);
                            timestamp_now = millis();
                            time_started_arduino = timestamp_now;
                            Serial.flush();
                            n++;
                            op = true;
                            reset = false;
                            started = true;
                            main_dataprint();
                     }
              }
              else if(rbytes[n] == 'x'){//DATA COLLECTION STOPS 
                      Serial.println("Stopped!"); // if line =="Stopped!": hasStopped = True;
                      Serial.flush();
                      n++;
                      op = false;
                      reset = true;
                      rotation();   
              }
              else if (isDigit(rbytes[n]) || rbytes[n] == '-'){ // 'digit' = new load cell calibration has been sent
                      caliStr += (char)rbytes[n]; // put calibration factor into string
                      caliLoop = true; // to start calibration process (loop) after receiving full calibration factor (exiting for loop)
              }
              else if (rbytes[n] == 'c'){ // 'c' = end calibration process
                      showF = false;
                      caliLoop = false; // to stop calibration process
              }
              else if(rbytes[n] == 't'){// TARE 
                       scale.set_scale();
                       scale.tare(); //Reset the scale to 0
               }
               else{
                       main_dataprint();
               }
    }
    else{
        if (caliLoop == true){ // starts calibration process (needs to be outside of for loop)
          showF = true; 
        }
        main_dataprint();
    }
    delay(.5); // delay needed?      
}
  //MAIN OPERATION - Serial sending data to RPi
void main_dataprint()
{  
  if(op == true){  
      scale.set_scale(calibra);//force sensor calibration
      value_encoderTicks = _EncoderTicks; // get Encoder Ticks 
      value_encoderDegrees = map(value_encoderTicks, 0, 1023, 0, 359); // convert to degrees
      actualDiameter = value_encoderDegrees*wheelDiameter; // convert to actual distance traveled
      kgs = scale.get_units(); //something is going wrong here
      Newtons = kgs*kg_Newtons; // convert to Newtons.
      timestamp_now = millis();
      time_elapsed_arduino = timestamp_now - time_started_arduino;
      
      Serial.print(actualDiameter);
      Serial.print('|');
      Serial.print(Newtons,3);
      Serial.print('|');
      Serial.print(time_elapsed_arduino);
      Serial.println();
      
      Serial.flush();//wait until data is written to Pi
      delay(2); // delay needed?      
  }
}

// Encoder Function
void rotation(){
    if (reset == false){
        _EncoderBSet = digitalReadFast(c_EncoderPinB);   // read the input pin
    #ifdef EncoderIsReversed
        _EncoderTicks += _EncoderBSet ? -1 : +1;
    #else
        _EncoderTicks -= _EncoderBSet ? -1 : +1;
    #endif
    }
    if(reset == true){
        _EncoderTicks = 0;
    }
}
