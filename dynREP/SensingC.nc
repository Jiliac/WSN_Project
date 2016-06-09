
/**
 * Oscilloscope demo application. See README.txt file in this directory.
 * @author David Gay
 */
#include "Timer.h"
#include "Sensing.h"
#include "routing_table.h"
#include <math.h>

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

    /* Current local state - interval and accumulated readings */
    sensing_t local;
    control_t rep;
    update_t last_received;             // used during the AWAKE_ASSOC phase

    uint16_t SIM_THRESHOLD = 2000;      // heavily dependent on the sensed data...
    int8_t sleeping_counter = 0;
    int8_t SLEEPING_TIME_MAX = 80;      // when sleeping_counter reach this value, waking up 
    int8_t AWAKE_TIME_MAX = 10;
    int8_t AWAKE_TIME_MIN = 2;
    int8_t next_sleeping_time;
    int8_t next_awake_time;
    float APP_CRITICALITY = 3;         // define how the application is critical. Key user input
                                        // define how long a node will spend sleeping and in awake-assoc state
                                        // if positive, critical app. If negative, will spend more time sleeping
                                        // 0 = original mode, sleeping time is constant
    bool wanting_to_sleep = FALSE;      // to use before acknowlgdement reception of a JOIN packet
    bool in_sleep = FALSE;              // two arguments defining the state of a node. If both are false, then in REP mode
    bool awake_assoc = FALSE;
    uint16_t my_rep = -1;               // if in ASSOCiate mode, then to store the REPresenting node.
    uint8_t to_read0, to_read1;

    message_t sendBuf;
    bool sendBusy;

    uint8_t reading; /* 0 to NREADINGS */

    void report_problem(uint8_t from) { dbg("Report", "!!!!!!!!!  There is a problem somewhere !!!!!!! - %hhu\n", from); }
    void report_sent() { dbg("Networking", "Sent something\n"); }
    void report_received(uint8_t len) { dbg("Networking", "Received something - size: %hhu\n", len); }


    // REP control packets
    void send_control(uint16_t receiver_id, uint8_t type) {
        rep.receiver_id = receiver_id;
        rep.type = type;
        if(!sendBusy) {
            memcpy(call AMSend.getPayload(&sendBuf, sizeof(rep)), &rep, sizeof(rep));
            if (call AMSend.send(AM_BROADCAST_ADDR, &sendBuf, sizeof(rep)) == SUCCESS)
                sendBusy = TRUE;
            dbg("REP", "sending a control packet :-)\n");
        }
    }
    void send_leave(uint16_t receiver_id) {
        dbg("Report", "Node %hu is leaving ASSOC mode\n");
        my_rep = -1;
        send_control(receiver_id, 1);
    }
    void send_join(uint16_t receiver_id) {
        dbg("Report", "Node %hu take node %hu as representative\n", local.id, receiver_id);
        my_rep = receiver_id;
        send_control(receiver_id, 2);
    }
    void send_ack(uint16_t receiver_id) {send_control(receiver_id, 4);}

    // similarity computing
    uint16_t sim(uint16_t ext_value) {
        uint16_t diff;
        to_read0 = (reading - 1) % NREADINGS;
        diff = ext_value - local.readings[to_read0];
        dbg("REP", "Compared values are, mine: %hu and the one I received: %hu\n", local.readings[to_read0], ext_value);
        if(diff < 0)
            return -diff;
        else
            return diff; 
    }

    void set_next_awake_time() {
        float tmp = 1.0*next_sleeping_time / SLEEPING_TIME_MAX;
        tmp = 1-tmp;    // This implies awake_time is computed with same criticality as sleeping_time
                        // A future improvement could be to compute it with a different
                        // and evaluate how much benefits there is
        next_awake_time = (tmp * AWAKE_TIME_MAX + 0.5);
        if(AWAKE_TIME_MIN > next_awake_time)
            next_awake_time = AWAKE_TIME_MIN;
        if(AWAKE_TIME_MIN > next_awake_time)
            next_awake_time = AWAKE_TIME_MIN;
    }
    void set_next_sleeping_time(uint16_t difference){
        float tmp;
        float r;
        if(APP_CRITICALITY < 0)
            r = -1.0/APP_CRITICALITY;
        else
            r = APP_CRITICALITY;
        tmp = (difference*1.0) / SIM_THRESHOLD;
        tmp = powf(1.0-tmp, r);
        next_sleeping_time = tmp * SLEEPING_TIME_MAX;
    }
    void sleep() {
        dbg("Sleep", "Sleeping - my REP is: %hu - next sleeping time is: %hu\n", my_rep, next_sleeping_time);
        sleeping_counter = 0;
        reading = 0;
        in_sleep = TRUE;
    }

    event void Boot.booted() {
        dbg("Boot", "Booted\n");
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
        uint16_t difference;
        if(local.id != TARGET){
            if(!in_sleep && !awake_assoc){
                report_received(len);

                if(len == sizeof(update_t)){
                    update_t *omsg = payload;

                    difference = sim(omsg->readings[1]);
                    if(SIM_THRESHOLD > difference) {
                        set_next_sleeping_time(difference);
                        dbg("REP", "Should go to sleep now !!\n");
                        wanting_to_sleep = TRUE;
                        send_join(omsg->id);
                    }
                } else if(len == sizeof(control_t)){
                    control_t *omsg = payload;
                    uint8_t type = omsg->type;
                    if(type & 1){
                        dbg("REP", "And now receiving a leave packet \\o/\n");
                        if(local.id == omsg->receiver_id)
                            send_ack(omsg->id);
                    }
                    else if(type & 2){
                        dbg("REP", "And now receiving a join packet \\o/\n");
                        if(local.id == omsg->receiver_id)
                            send_ack(omsg->id);
                    }
                    else if(type & 4){
                        dbg("REP", "And now receiving an ack packet \\o/\n");
                        if(wanting_to_sleep){
                            wanting_to_sleep = FALSE;
                            sleep();
                        }
                    }
                }
            } else if (awake_assoc) {
                report_received(len);

                if(len == sizeof(update_t)){
                    update_t *omsg = payload;
                    if(omsg->id == my_rep){
                        last_received = *omsg;
                    }
                }
            }
        }

        return msg;
    }

    event void Timer.fired() {
        uint16_t difference;
        if(!in_sleep && !awake_assoc){
            if (reading == NREADINGS)
            {
                if (!sendBusy && sizeof local <= call AMSend.maxPayloadLength())
                {
                    // Don't need to check for null because we've already checked length above
                    memcpy(call AMSend.getPayload(&sendBuf, sizeof(local)), &local, sizeof local);
                    if (call AMSend.send(TARGET, &sendBuf, sizeof local) == SUCCESS ){
                        dbg("Networking", "Trying to send info to base station\n");
                        sendBusy = TRUE;
                    }
                }
                if (!sendBusy)
                    report_problem(1);
                
                reading = 0;

            } else if(!sendBusy && (reading%2) == 0) {
                update_t to_send;
                to_send.id = local.id;
                to_read0 = (reading-2) % NREADINGS;
                to_read1 = (reading-1) % NREADINGS;
                to_send.readings[0] = local.readings[to_read0];
                to_send.readings[1] = local.readings[to_read1];
                memcpy(call AMSend.getPayload(&sendBuf, sizeof(to_send)), &to_send, sizeof to_send);
                if (call AMSend.send(AM_BROADCAST_ADDR, &sendBuf, sizeof to_send) == SUCCESS){
                    dbg("Networking", "Trying to send info around me\n");
                    sendBusy = TRUE;
                }
                if (!sendBusy)
                    report_problem(1);

            }
            if (call Read.read(local.id) != SUCCESS)
                report_problem(2);
        } else {
            if(in_sleep && ++sleeping_counter == next_sleeping_time) {
                in_sleep = FALSE;
                awake_assoc = TRUE;
                set_next_awake_time();
                dbg("Sleep", "Waking up - my REP is: %hu\n", my_rep);
                dbg("Sleep", "next awake assoc time: %hu\n", next_awake_time);
                sleeping_counter = 0;
            } else if(awake_assoc) {
                if(++sleeping_counter == next_awake_time) {
                    difference = sim(last_received.readings[1]);
                    if(SIM_THRESHOLD > difference) {
                        dbg("Sleep", "Going to sleep again after awake-assoc\n");
                        awake_assoc = FALSE;
                        set_next_sleeping_time(difference);
                        sleep();
                    } else {
                        dbg("Sleep", "Waking up fully\n");
                        awake_assoc = FALSE;
                        send_leave(my_rep);
                    }
                } else if(call Read.read(local.id) != SUCCESS){ // Read while the sleeping counter didn't reach AWAKE_TIME
                    report_problem(5);
                }
            }
        }
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
            dbg("Report", "Reading something - Data: %hu\n", data);
        local.readings[reading++] = data;
    }

#ifdef DYMO_MONITORING
    event void DymoMonitor.msgReceived(message_t * msg){
        dbg("messages", "Monitor: Dymo msg received\n");
    }

    event void DymoMonitor.msgSent(message_t * msg){
        dbg("messages", "Monitor: Dymo msg sent\n");
    }

    event void DymoMonitor.routeDiscovered(uint32_t delay, addr_t target){
        dbg("messages", "Monitor: Route for %u discovered in %lu milliseconds\n", target, delay);
    }
#endif
}
