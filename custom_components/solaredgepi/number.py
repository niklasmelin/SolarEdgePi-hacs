from homeassistant.components.number import NumberEntity

class SolarEdgeNumber(NumberEntity):
    def __init__(self, controller, name, key, min_value=0, max_value=10000):
        self._controller = controller
        self._name = name
        self._key = key
        self._state = controller.status["control"].get(key, 0)
        self._min = min_value
        self._max = max_value

    @property
    def name(self):
        return self._name

    @property
    def value(self):
        return self._state

    @property
    def min_value(self):
        return self._min

    @property
    def max_value(self):
        return self._max

    async def async_set_value(self, value: float):
        await self._controller.send_control({self._key: value})
        self._state = value
        self.async_write_ha_state()
