import datetime
import logging
import time
from typing import List, Tuple, Union

from src.device_manager import DeviceManager
from src.global_constants import *
from src.log_config import get_basic_formatter
from src.sensor_manager import SensorManager
from src.system_status import SystemInfoManager, CycleData

handler = logging.FileHandler('logs/controllers.log')
handler.setFormatter(get_basic_formatter())


def seconds_since(dt: datetime.datetime) -> float:
    return (datetime.datetime.now() - dt).total_seconds()


class MediaExchangeController:
    """Controls the exchange of media through the reactor."""

    flow_per_cycle: float
    cycles_schedule: List[Tuple[datetime.datetime, float]]

    next_cycle_time: datetime.datetime
    next_next_cycle_time: datetime.datetime
    time_between_cycles: datetime.timedelta

    dm: DeviceManager
    sm: SensorManager
    sys_info: SystemInfoManager
    cd: CycleData

    def __init__(self, volume: Union[float, None], flow_rate: float, cycles_per_hour: int,
                 sys_info: SystemInfoManager, dm: DeviceManager,
                 sm: SensorManager) -> None:
        """
        Initializes a media exchange controller that ensures that spent media is
        continually replaced with fresh media.

        :param volume: Volume of reactor, ml. If None, assumes reactor is empty
            and calculates by filling reactor.
        :param flow_rate: Volumes to replace per hour
        :param cycles_per_hour: Number of media exchange cycles to undergo per
            hour
        :param sys_info: stores system info
        :param dm: allows for control of devices
        :param sm: allows for control of sensors
        :param cd: stores cycle data
        :return: None
        """

        self.logger = logging.getLogger('Media Exchange Controller')
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.DEBUG)

        self.dm = dm
        self.sm = sm
        self.sys_info = sys_info
        self.cd = sys_info.get_cycle_data()

        do_cycle_delay = DELAY_FIRST_CYCLE
        if volume is None:
            volume = self._fill_reactor()
            if volume is None:
                return
            do_cycle_delay = True

        self.sys_info.set_reactor_volume(volume)
        flow_per_hour = volume * flow_rate
        self.flow_per_cycle = flow_per_hour / cycles_per_hour
        mins_between_cycles = 60 / cycles_per_hour
        self.time_between_cycles = datetime.timedelta(minutes=mins_between_cycles)

        self.next_cycle_time = datetime.datetime.now()
        if do_cycle_delay:
            self.next_cycle_time = self.next_cycle_time + \
                                   self.time_between_cycles + FIRST_CYCLE_DELAY
        self.next_next_cycle_time = self.next_cycle_time + \
                                    self.time_between_cycles

        # Print string with media cycling configuration information.
        next_cycle_str = self.next_cycle_time.strftime("%m/%d/%Y %H:%M:%S")

        mins = self.time_between_cycles.seconds // 60
        secs = self.time_between_cycles.seconds - mins * 60

        logging.info(
            f"Configuring media cycling. Will cycle {flow_rate:.2f}vols/hour "
            f"by performing {cycles_per_hour:.0f} cycles every hour each moving"
            f" {self.flow_per_cycle:.2f}mls of media per cycle. The first cycle"
            f" is planned for {next_cycle_str:s}, after which cycles will occur"
            f" every {mins:2.0f} minutes and {secs:2.0f} seconds.")


        sys_info.set_next_cycle(self.next_cycle_time)

    def _fill_reactor(self) -> Union[float, None]:
        """Fills an empty bioreactor, returns volume required to fill the
        reactor."""
        self.logger.info("Filling bioreactor.")
        if self.sm.wl_exceeded():
            self.sys_info.set_error_state('Media already at sensor during '
                                          'filling procedure.')
            self.logger.error("Media already at sensor during filling "
                              "procedure.")

        self.cd.__init__(REACTOR_MAX_VOLUME)
        self.sys_info.begin_media_cycle()
        self.sys_info.notify_observers()

        max_ontime = REACTOR_MAX_VOLUME / MEDIA_IN_FLOWRATE

        self.logger.info("Beginning Media Addition.")
        self.logger.info(
            'Adding at most ' + str(REACTOR_MAX_VOLUME) + 'mLs.')
        start_time = self.dm.get_inlet_ontime()
        self.cd.state = 'fill'
        self.dm.turn_on_inlet()

        while self.dm.get_inlet_ontime() - start_time < max_ontime \
                and not self.sm.wl_exceeded():
            self.cd.inlet_ontime = self.dm.get_inlet_ontime() - start_time
            self.sys_info.notify_observers()
            time.sleep(ULTRA_FAST_TICK)

        self.dm.turn_off_inlet()

        if self.dm.get_inlet_ontime() - start_time > max_ontime:
            self.sys_info.set_error_state('Vessel filled without triggering water'
                                          'level sensor.')
            self.logger.error("Sensor failed to detect fluid level even after "
                              "reaching max vessel volume.")
            return None

        self.cd.state = 'done'
        self.logger.info(
            ('Media addition complete. Pump ran for {runtime:.2f} seconds, '
             'adding {volume:.2f} mls of media before reaching the sensor.'
             ).format(runtime=self.dm.get_inlet_ontime() - start_time,
                      volume=self.cd.get_in_vol()))

        self.sys_info.notify_observers()
        self.sys_info.update_dispensed_volumes()
        self.sys_info.end_media_cycle()

        return self.cd.get_in_vol()

    def _iterate_cycles(self) -> None:
        """Calculates next cycle times."""
        self.next_cycle_time = self.next_next_cycle_time
        self.next_next_cycle_time = self.next_cycle_time + \
                                    self.time_between_cycles

    def cycle_check(self) -> None:
        """Checks if a scheduled cycle needs to be performed."""
        if self.next_next_cycle_time < datetime.datetime.now():
            self.logger.critical("Missed cycle at " +
                                 self.next_cycle_time.strftime("%m/%d/%Y,"
                                                               " %H:%M:%S."))
            self.sys_info.set_error_state('Fill cycle missed.')

        cycle_complete = False
        if self.next_cycle_time < datetime.datetime.now():
            self._iterate_cycles()
            self.sys_info.set_next_cycle(self.next_cycle_time)

            # Do nothing if currently in error state.
            if self.sys_info.get_state() == 'error':
                return

            # Proceed with media exchange.
            self.cd.__init__(self.flow_per_cycle)
            self.sys_info.begin_media_cycle()
            self.sys_info.notify_observers()
            cycle_complete = self.flow_cycle()

        if cycle_complete:
            self.sys_info.update_dispensed_volumes()
            self.sys_info.end_media_cycle()

    def flow_cycle(self) -> bool:
        """
        Attempts to cycle <flow_per_cycle> mls of media through the chemostat,
        first removing media, and then adding it.

        Uses the water level sensor to ensure that the media exchange is
        successful.

        Updates the cycle data and system info throughout the process.

        NOTE: Can result in system entering error state.
        """

        # Check water level.
        self.logger.info("Beginning Media Exchange. " +
                         self.sm.get_media_level_string())

        target_ontime = self.flow_per_cycle / MEDIA_OUT_FLOWRATE

        # Turn off stirring to give consistent water level.
        if self.dm.hotplate_is_on():
            self.dm.turn_off_hotplate()

        if self.dm.air_pump_is_on():
            self.dm.turn_off_air_pump()

        # Wait for media to become still.
        if MEDIA_CALMING:
            time.sleep(30)

        self.logger.info('Beginning media removal.')

        # Remove media.
        success = self._remove_media(target_ontime)
        if not success:
            return False
        if MEDIA_CALMING:
            time.sleep(5)

        # Replace media.
        success = self._add_media(target_ontime)
        if not success:
            return False

        if MEDIA_CALMING:
            time.sleep(5)

        # Calibrate media level.
        success = self._calibrate()
        if not success:
            return False

        if MEDIA_CALMING:
            time.sleep(5)

        return True

    def _remove_media(self, target_ontime: bool):
        """Remove a given amount of media by running the pump for
        <target_ontime>."""
        self.logger.info('Removing {:.2f}mls'.format(self.flow_per_cycle))
        self.logger.info('Turning outlet on for {:.2f}'.format(target_ontime) +
                         " seconds.")
        self.cd.state = 'drain'
        start_time = self.dm.get_outlet_ontime()
        self.dm.turn_on_outlet()
        self.dm.turn_on_air_pump()


        # Wait for media removal to complete.
        while self.dm.get_outlet_ontime() - start_time < target_ontime:
            self.sm.update_readings()
            self.cd.outlet_ontime = self.dm.get_outlet_ontime() - start_time
            self.sys_info.notify_observers()
            time.sleep(ULTRA_FAST_TICK)

        self.dm.turn_off_outlet()
        self.dm.turn_off_air_pump()

        self.logger.info("Media removal complete. " +
                         self.sm.get_media_level_string())

        # Check if media level exceeded even after removal.
        # Water level sensor likely producing incorrect reading.
        if self.sm.wl_exceeded():
            self.logger.critical("Water level exceeded even after media "
                                 "removal.")
            self.sys_info.set_error_state("Water level exceeded even after media "
                                 "removal.")
            return False

        return True


    def _add_media(self, target_ontime: float) -> bool:
        """Add a given amount of media by running the pump for
        <target_ontime>."""

        self.logger.info("Beginning Media Addition.")
        self.logger.info(
            'Attempting to add ' + str(self.flow_per_cycle) + 'mls.')
        start_time = self.dm.get_inlet_ontime()
        self.cd.state = 'fill'
        self.dm.turn_on_inlet()

        while self.dm.get_inlet_ontime() - start_time < target_ontime \
                and not self.sm.wl_exceeded():
            self.cd.inlet_ontime = self.dm.get_inlet_ontime() - start_time
            self.sys_info.notify_observers()
            time.sleep(ULTRA_FAST_TICK)

        self.dm.turn_off_inlet()
        self.cd.inlet_ontime = self.dm.get_inlet_ontime() - start_time

        # Overfilled media.
        if self.cd.inlet_ontime < target_ontime:
            self.cd.state = 'over'
            self.logger.info(
                ('Media addition complete. Pump ran for {runtime:.2f} seconds, '
                 'adding {volume:.2f} mls of media before reaching the sensor.'
                 ).format(runtime=self.cd.inlet_ontime,
                          volume=self.cd.get_in_vol()))
        else:
            self.cd.state = 'under'
            self.logger.info(
                ('Media addition complete. Pump ran for {runtime:.2f} seconds, '
                 'adding {volume:.2f} mls of media and did not reach the sensor.'
                 ).format(runtime=self.cd.inlet_ontime,
                          volume=self.cd.get_in_vol()))

        self.sys_info.notify_observers()

        return True

    def _calibrate(self) -> bool:
        """Calibrate media level to account for adding error."""
        # Calculate maximum amount to add.
        max_calib_amt = self.flow_per_cycle
        max_calib_time = max_calib_amt / MEDIA_IN_FLOWRATE

        self.logger.info('Adding at most {:.2f}mls to calibrate media level.' \
                         .format(max_calib_amt))

        self.cd.state = 'calib'

        org_runtime = self.cd.inlet_ontime
        calib_start_time = self.dm.get_inlet_ontime()
        self.dm.turn_on_inlet()

        while self.dm.get_inlet_ontime() - calib_start_time < max_calib_time \
                and not self.sm.wl_exceeded():
            self.cd.inlet_ontime = self.dm.get_inlet_ontime() - \
                                   calib_start_time + org_runtime
            self.sys_info.notify_observers()
            time.sleep(ULTRA_FAST_TICK)

        self.dm.turn_off_inlet()

        rt = self.dm.get_inlet_ontime() - calib_start_time

        if rt < max_calib_time:
            self.cd.state = 'done'
            self.logger.info(
                ('Calibration complete. Pump ran for {runtime:.2f} seconds, '
                 'adding {volume:.2f} mls of media before reaching the sensor.'
                 ).format(runtime=rt, volume=rt * MEDIA_IN_FLOWRATE))
            self.sys_info.notify_observers()
        else:
            self.cd.state = 'error'
            self.logger.info(
                ('Calibraion failed. Pump ran for {runtime:.2f} seconds, '
                 'adding {volume:.2f} mls of media and did not reach the sensor.'
                 ).format(runtime=rt, volume=rt * MEDIA_IN_FLOWRATE))

            self.logger.critical("Calibration failed. Water level sensor may be "
                                 "failing.")
            self.sys_info.set_error_state("Calibration Failed, Water level not reached.")
            return False

        return True





