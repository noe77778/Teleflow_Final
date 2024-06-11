/*
  FILE: ATdebug.ino
  AUTHOR: Kaibin
  PURPOSE: Test functionality
*/

#define TINY_GSM_MODEM_SIM7600
#define TINY_GSM_RX_BUFFER 1024 // Set RX buffer to 1Kb
#define SerialAT Serial1
#define SMS_TARGET  "+527222336099"

#define DUMP_AT_COMMANDS

#define S1_P1     12  // split #1 Palco #1
#define S1_P2     13  // split #1 Palco #2
#define S1_P3     14  // split #1 Palco #3
#define S1_P4     15  // split #1 Palco #4

#define GSM_PIN ""

// Your GPRS credentials, if any
const char apn[]  = "YOUR-APN";     //SET TO YOUR APN
const char gprsUser[] = "";
const char gprsPass[] = "";

#include <TinyGsmClient.h>
#include <SPI.h>
#include <SD.h>
#include <Ticker.h>
#include "utilities.h"

#include <array>

std::array<int, 40> TAPS_Table;

#ifdef DUMP_AT_COMMANDS  // if enabled it requires the streamDebugger lib
#include <StreamDebugger.h>
StreamDebugger debugger(SerialAT, Serial);
TinyGsm modem(debugger);
#else
TinyGsm modem(SerialAT);
#endif

int counter, lastIndex, numberOfPieces = 24;
String pieces[24], input;

bool reply = false;

void BUCK_PINS () {
    pinMode(S1_P1, OUTPUT);
    pinMode(S1_P2, OUTPUT);
    pinMode(S1_P3, OUTPUT);
    pinMode(S1_P4, OUTPUT);
    digitalWrite(S1_P1, HIGH);
    digitalWrite(S1_P2, HIGH);
    digitalWrite(S1_P3, HIGH);
    digitalWrite(S1_P4, HIGH);
}

void create_lut() {
    // Populate the lookup table with 40 values by repeating {12, 13, 14, 15}
    for (int i = 0; i < 40; ++i) {
        TAPS_Table[i] = 12 + (i % 4);
    }
}

void modem_on() {
    pinMode(LED_PIN, OUTPUT);
    digitalWrite(LED_PIN, HIGH);
    pinMode(MODEM_PWRKEY, OUTPUT);
    digitalWrite(MODEM_PWRKEY, HIGH);
    delay(300); //Need delay
    digitalWrite(MODEM_PWRKEY, LOW);
    pinMode(MODEM_FLIGHT, OUTPUT);
    digitalWrite(MODEM_FLIGHT, HIGH);

    int i = 40;
    Serial.print(F("\r\n# Startup #\r\n"));
    Serial.print(F("# Sending \"AT\" to Modem. Waiting for Response\r\n# "));
    while (i) {
        SerialAT.println(F("AT"));
        Serial.print(F("."));
        delay(500);

        if (SerialAT.available()) {
            String r = SerialAT.readString();
            Serial.print("\r\n# Response:\r\n" + r);
            if (r.indexOf("OK") >= 0) {
                reply = true;
                break;
            } else {
                Serial.print(F("\r\n# "));
            }
        }

        if (Serial.available() && !reply) {
            Serial.read();
            Serial.print(F("\r\n# Modem is not yet online."));
            Serial.print(F("\r\n# Sending \"AT\" to Modem. Waiting for Response\r\n# "));
        }

        if (i == 35) {
            Serial.print(F("\r\n# Modem did not yet answer. Probably Power loss?\r\n"));
            Serial.print(F("# Sending \"AT\" to Modem. Waiting for Response\r\n# "));
        }
        delay(500);
        i--;
    }
    Serial.println(F("#\r\n"));
}

String incoming;
String send_s;

void setup() {

   
    BUCK_PINS();
    create_lut();
    Serial.begin(115200); // Set console baud rate
    SerialAT.begin(115200, SERIAL_8N1, MODEM_RX, MODEM_TX);
    delay(100);

    String textForSMS = "Holi APS";

    modem_on();
    if (reply) {
        Serial.println(F("*"));
        Serial.println(F(" You can now send AT commands"));
        Serial.println(F(" Enter \"AT\" (without quotes), and you should see \"OK\""));
        Serial.println(F(" If it doesn't work, select \"Both NL & CR\" in Serial Monitor"));
        Serial.println(F(" DISCLAIMER: Entering AT commands without knowing what they do"));
        Serial.println(F(" can have undesired consequences..."));
        Serial.println(F("*\n"));

        // Uncomment to read received SMS
        // SerialAT.println("AT+CMGL=\"ALL\"");
    } else {
        Serial.println(F("*"));
        Serial.println(F(" Failed to connect to the modem! Check the baud and try again."));
        Serial.println(F("*\n"));
    }

    // modem.sendSMS(SMS_TARGET, textForSMS);
    // delay(1000);

    SerialAT.println("AT+CPMS=\"SM\",\"SM\",\"SM\"");
    delay(500);
    if (SerialAT.available()) {
            String r = SerialAT.readString();
            Serial.print("\r\n# Response:\r\n" + r);
            if (r.indexOf("OK") >= 0) {
                //reply = true;
                //break;
                Serial.println(F("Memory set to prefered type"));
            } else {
                Serial.println(F("Memory not set to prefered type"));
            }
        }
    SerialAT.println("AT+CMGF=1");
    delay(500);
    if (SerialAT.available()) {
            String r = SerialAT.readString();
            Serial.print("\r\n# Response:\r\n" + r);
            if (r.indexOf("OK") >= 0) {
                //reply = true;
                //break;
                Serial.println(F("Set to text mode"));
            } else {
                Serial.println(F("Could not set to text mode"));
            }
        }
    SerialAT.println("AT+CMGD=1,4");
    delay(500);
    if (SerialAT.available()) {
            String r = SerialAT.readString();
            Serial.print("\r\n# Response:\r\n" + r);
            if (r.indexOf("OK") >= 0) {
                //reply = true;
                //break;
                Serial.println(F("Cleared MEMORY"));
            } else {
                Serial.println(F("Could not CLEAR MEMORY"));
            }
        }
      
}

String update_MS2() {
    incoming = "";
    if (SerialAT.available()) {
        incoming = SerialAT.readString();
        incoming.trim();
        Serial.println(incoming);
        if (incoming.substring(0, 5) == "+CMTI") {
            int idx = incoming.indexOf(",");
            if (idx > 0 ) { // idx + 3 <= incoming.length()
                String idx_msg_s = incoming.substring(idx + 1, idx + 3);
                idx_msg_s.trim();
                send_s = "AT+CMGR=" + idx_msg_s;
                String p = "PASS";
                if (idx_msg_s == "28") p = "PASS_C";
                return p;
            }
        }
    }
    return "NO_PASS";
}

void update_MS() {
    if (SerialAT.available()) {
        Serial.write(SerialAT.read());
    }

    if (Serial.available()) {
        SerialAT.write(Serial.read());
    }
    delay(1);
}

String receive_msg() {
    String message = "";
    if (SerialAT.available()) {
        String teststr = SerialAT.readString();
        teststr.trim();
        int response_idx = teststr.indexOf("OK");
        int last_quote = teststr.lastIndexOf('"');
        if (response_idx > 0 && last_quote > 0 && last_quote < response_idx) {
            message = teststr.substring(last_quote + 1, response_idx);
            message.trim();
            //return teststr2; // Trim any extra whitespace
        }
    }
    return message;
}




void clearModemMemory() {
    SerialAT.println("AT+CMGD=1,4");
    delay(500);
    unsigned long startTime = millis();
    const unsigned long timeout = 5000; // 5 seconds timeout

    while (millis() - startTime < timeout) {
        if (SerialAT.available()) {
            String response = SerialAT.readString();
            Serial.println("Modem response: " + response);
            if (response.indexOf("OK") != -1) {
                Serial.println("Modem memory cleared");
                return;
            }
        }
        delay(10); // Short delay to prevent busy-waiting
    }
    Serial.println("Timeout: Failed to clear modem memory");
}


void processReceivedMessage(const String& message) {
    Serial.println(message);

    int underscore = message.indexOf("_");
    if (underscore > 0) {
        String idStr = message.substring(0, underscore);
        idStr.trim();
        String cmdStr = message.substring(underscore + 1);
        cmdStr.trim();

        Serial.print("idStr: ");
        Serial.println(idStr);
        Serial.print("cmdStr: ");
        Serial.println(cmdStr);
        Serial.print("cmdStr (ASCII): ");
        for (int i = 0; i < cmdStr.length(); i++) {
            Serial.print((int)cmdStr[i]);
            Serial.print(" ");
        }
        Serial.println();

        int id = idStr.toInt() - 1;

        if (id >= 0 && id < TAPS_Table.size()) {
            handleCommand(id, cmdStr);
        } else {
            Serial.println("Invalid indices received");
        }
    } else {
        Serial.println("Invalid message format");
    }
}

void handleCommand(int id, const String& cmdStr) {
    if (cmdStr == "ON") {
        Serial.println("Turning ON:");
        Serial.println(TAPS_Table[id]);
        digitalWrite(TAPS_Table[id], LOW);
    } else if (cmdStr == "OFF") {
        Serial.println("Turning OFF:");
        Serial.println(TAPS_Table[id]);
        digitalWrite(TAPS_Table[id], HIGH);
    } else {
        Serial.println("Unknown command");
    }
}

////////////////////////////// MAIN ////////////////////////////////////////////////////////////////////////////////////////

void loop() {
    String received_message;

    String buff_msg = update_MS2(); // Check for any incoming message, just checking serial info sent by SIM7600
    delay(1);
    
    if (buff_msg == "PASS" || buff_msg == "PASS_C") { // If there is an incoming message, trigger command to read it
        SerialAT.println(send_s);
        delay(500);
        received_message = receive_msg(); // storing received message on string for later
        delay(500);
        
        if (buff_msg == "PASS_C") { // In case the MEM is almost empty (28 messages), we need to clear
            clearModemMemory();
        }
    }

    // Actual control 
    if (!received_message.isEmpty())  {
      processReceivedMessage(received_message);
    }
}

      
