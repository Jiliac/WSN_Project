
/**
 * Oscilloscope demo application. See README.txt file in this directory.
 * @author David Gay
 */
#define DYMO_MONITORING
configuration SensingAppC { }
implementation
{
    components SensingC, MainC, DymoNetworkC,
        new TimerMilliC(), new ConstantSensorC(uint16_t, 0xbeef) as Sensor;
        //new SineSensorC() as Sensor;

    SensingC.Boot          -> MainC;
    SensingC.RadioControl  -> DymoNetworkC;
    SensingC.AMSend        -> DymoNetworkC.MHSend[1];
    SensingC.Receive       -> DymoNetworkC.Receive[1];
    SensingC.Timer         -> TimerMilliC;
    SensingC.Read          -> Sensor;

#ifdef DYMO_MONITORING
    SensingC.DymoMonitor -> DymoNetworkC;
#endif
}
