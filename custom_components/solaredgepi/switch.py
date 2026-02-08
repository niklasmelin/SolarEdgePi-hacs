from homeassistant.components.switch import SwitchEntity

class SolarEdgeSwitch(SwitchEntity):
    def __init__(self, controller, name, key):
        self._controller = controller
        self._name = name
        self._key = key
        self._state = controller.status["control"].get(key, False)

    @property
    def name(self):
        return self._name

    @property
    def is_on(self):
        return self._state

    async def async_turn_on(self, **kwargs):
        await self._controller.send_control({self._key: True})
        self._state = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        await self._controller.send_control({self._key: False})
        self._state = False
        self.async_write_ha_state()
