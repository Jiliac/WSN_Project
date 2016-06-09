
/**
 * Oscilloscope demo application. See README.txt file in this directory.
 * @author David Gay
 */
#include "Timer.h"
#include "Sensing.h"
#include "routing_table.h"

module SensingC @safe()
{
    uses {
        interface Boot;
        interface SplitControl as RadioControl;
        interface AMSend;
        interface Receive;
        interface Timer<TMilli>;
        interface Read<uint16_t>;
    }
#ifdef DYMO_MONITORING
    uses interface DymoMonitor;
#endif
}
implementation
{
    enum{
        TARGET = 1,
    };

    message_t sendBuf;
    bool sendBusy;

    /* Current local state - interval and accumulated readings */
    sensing_t local;

    uint8_t reading; /* 0 to NREADINGS */

    void report_problem(uint8_t from) { dbg("Report", "!!!!!!!!!  There is a problem somewhere !!!!!!! - %hhu - %s\n", from, sim_time_string()); }
    void report_sent() { dbg("Networking", "Sent something - %s\n", sim_time_string()); }
    void report_received(uint8_t len) { dbg("Networking", "Received something - size: %hhu - %s\n", len, sim_time_string()); }

    event void Boot.booted() {
        dbg("Boot", "Booted - %s\n", sim_time_string());
        local.interval = DEFAULT_INTERVAL;
        local.id = TOS_NODE_ID;
        if (call RadioControl.start() != SUCCESS)
            report_problem(0);
    }

    void startTimer() {
        if(local.id != TARGET) {
            call Timer.startPeriodic(local.interval);
            reading = 0;
        }
    }

    event void RadioControl.startDone(error_t error) {
        startTimer();
    }

    event void RadioControl.stopDone(error_t error) {}

    event message_t* Receive.receive(message_t* msg, void* payload, uint8_t len) {
        sensing_t *omsg = payload;

        report_received(len);

        return msg;
    }

    event void Timer.fired() {
        if (reading == NREADINGS)
        {
            if (!sendBusy && sizeof local <= call AMSend.maxPayloadLength())
            {
                // Don't need to check for null because we've already checked length above
                memcpy(call AMSend.getPayload(&sendBuf, sizeof(local)), &local, sizeof local);
                if (call AMSend.send(TARGET, &sendBuf, sizeof local) == SUCCESS ){
                    dbg("Networking", "Trying to send info to base station - %s\n", sim_time_string());
                    sendBusy = TRUE;
                }
            }
            if (!sendBusy)
                report_problem(1);

        } else if(!sendBusy && (reading%2) == 0) {
            memcpy(call AMSend.getPayload(&sendBuf, sizeof(local)), &local, sizeof local);
            if (call AMSend.send(AM_BROADCAST_ADDR, &sendBuf, sizeof local) == SUCCESS ){
                dbg("Networking", "Trying to send info around me - %s\n", sim_time_string());
                sendBusy = TRUE;
            }
            if (!sendBusy)
                report_problem(1);

        }
        if (call Read.read(1) != SUCCESS)
            report_problem(2);
    }

    event void AMSend.sendDone(message_t* msg, error_t error) {
        if (error == SUCCESS)
            report_sent();
        else
            report_problem(3);

        sendBusy = FALSE;
    }

    event void Read.readDone(error_t result, uint16_t data) {
        if (result != SUCCESS)
        {
            data = 0xffff;
            report_problem(4);
        }
        if (reading < NREADINGS) 
            dbg("Report", "Reading something - Data: %hu - %s\n", data, sim_time_string());
        local.readings[reading++] = data;
    }

#ifdef DYMO_MONITORING
    event void DymoMonitor.msgReceived(message_t * msg){
        dbg("messages", "Monitor: Dymo msg received.\n");
    }

    event void DymoMonitor.msgSent(message_t * msg){
        dbg("messages", "Monitor: Dymo msg sent.\n");
    }

    event void DymoMonitor.routeDiscovered(uint32_t delay, addr_t target){
        dbg("messages", "Monitor: Route for %u discovered in %lu milliseconds.\n", target, delay);
    }
#endif
}
