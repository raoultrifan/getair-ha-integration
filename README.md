# getAir Home Assistant Integration

A custom Home Assistant integration for **getAir ComfortControl Pro BT and Smart Control Hub** mechanical heat-recovery ventilation systems, providing local-style cloud control via the getAir REST API (https://github.com/getaireu/REST-API).

---

## Features

- 🌀 **Fan entity** — full speed control (0.5–4.0) and ventilation mode selection
- 📊 **Sensors** — indoor temperature, humidity, air quality, fan speed, ventilation mode, runtime
- 🔄 **Auto token refresh** — handles OAuth2 authentication automatically
- ⏱️ **5-minute polling** — lightweight cloud polling via getAir REST API
- 🎛️ **Dashboard cards** — custom Lovelace cards included
- 🏠 **HACS compatible** — easy installation via HACS

---

## Supported Devices

- getAir ComfortControl Pro BT
- getAir Smart Control Hub
---

## Requirements

- Home Assistant 2023.1.0 or newer
- A getAir account linked to your device (via the getAir app)
- API access enabled by getAir support (email `info@getair.eu` to request)

> **Note:** API access is not enabled by default. You must contact getAir support and request API access for your account before this integration will work.

---

## Installation

### Via HACS (Recommended)

1. Open HACS in Home Assistant
2. Go to **Integrations**
3. Click the three dots menu → **Custom repositories**
4. Add `https://github.com/raoultrifan/getair-ha-integration` with category **Integration**
5. Find **getAir Integration** in HACS and click **Download**
6. Restart Home Assistant

### Manual Installation

1. Download or clone this repository
2. Copy the `custom_components/getair/` folder to your HA `config/custom_components/` directory
3. Restart Home Assistant

---

## Configuration

1. Go to **Settings → Integrations → Add Integration**
2. Search for **getAir**
3. Enter your getAir account email and password
4. The integration will automatically discover your device

![Add getAir interation](/images/getAir_Integration.png)

![Add getAir interation](/images/getAir_Integration_.png)

![Add getAir interation](/images/getAir_DeviceInfo.jpg)

![Add getAir interation](/images/getAir_Entities.png)

---

## Dashboard Cards

**You can play with the dasboard as you like, based on what environmental sensors you've installed in the room / rooms. Below are some examples of dashboard I've used.**

![Dashboard 1 Preview](/images/getAir_Dashboard_04.png)

![Dashboard 2 Preview](/images/getAir_Dashboard_02.png)

![Dashboard 3 Preview](/images/getAir_Dashboard_01.png)

![Dashboard 4 Preview](/images/getAir_Dashboard_02.png)


Three optional custom Lovelace cards are included in the `www/` folder:

### Installation

1. Copy all `.js` files from `www/` to your HA `config/www/` directory
2. Go to **Settings → Dashboards → (three dots) → Resources → Add Resource** for each file:
   - URL: `/local/getair-card.js` — Type: JavaScript Module
   - URL: `/local/getair-schedule-card.js` — Type: JavaScript Module
   - URL: `/local/getair-speed-scale.js` — Type: JavaScript Module
3. Refresh your browser

### getAir Control Card (`getair-card`)

A full control panel with speed slider, mode selector, and sensor readings.

```yaml
type: custom:getair-card
speed_entity: number.getair_fan_speed
mode_entity: select.getair_ventilation_mode
temperature_entity: sensor.getair_indoor_temperature
humidity_entity: sensor.getair_indoor_humidity
aiq_entity: sensor.getair_indoor_air_quality
```

### getAir Schedule Card (`getair-schedule-card`)

A read-only timeline viewer for your HA automations schedule.

```yaml
type: custom:getair-schedule-card
schedule:
  - time: "09:00"
    mode: Heat Recovery
    speed: 2.5
  - time: "21:30"
    mode: Heat Recovery
    speed: 1.5
  - time: "23:00"
    mode: Heat Recovery
    speed: 2.0
```

### getAir Speed Scale Card (`getair-speed-scale`)

A horizontal speed scale with tick marks and a glowing thumb. Tap any label to set speed directly.

```yaml
type: custom:getair-speed-scale
entity: fan.getair_comfortcontrol_pro_bt_getair_fan
speed_sensor: sensor.getair_comfortcontrol_pro_bt_fan_speed
min_speed: 0.5
max_speed: 4.0
step: 0.5
```

---

## Example Dashboard

Here's a full example dashboard combining Bubble Card, Button Card, Tile Card and the custom speed scale:

### Prerequisites (install via HACS Frontend)
- [Bubble Card](https://github.com/Clooos/Bubble-Card)
- [Mushroom Cards](https://github.com/piitaya/lovelace-mushroom)
- [Button Card](https://github.com/custom-cards/button-card)
- [Auto Entities](https://github.com/thomasloven/lovelace-auto-entities)

### Bubble Card (main control)

```yaml
type: custom:bubble-card
card_type: cover
entity: fan.getair_comfortcontrol_pro_bt_getair_fan
name: getAir SmartFan
icon: mdi:hvac
show_state: true
card_layout: large
scrolling_effect: false
icon_up: mdi:fan-chevron-up
icon_down: mdi:fan-chevron-down
open_service: script.getair_speed_increase
close_service: script.getair_speed_decrease
sub_button:
  main:
    - entity: fan.getair_comfortcontrol_pro_bt_getair_fan
      name: Left
      icon: mdi:arrow-left
      show_name: true
      show_state: false
      tap_action:
        action: call-service
        service: fan.set_preset_mode
        data:
          entity_id: fan.getair_comfortcontrol_pro_bt_getair_fan
          preset_mode: "Left (Normal)"
    - entity: fan.getair_comfortcontrol_pro_bt_getair_fan
      name: HR
      icon: mdi:heat-wave
      show_name: true
      show_state: false
      tap_action:
        action: call-service
        service: fan.set_preset_mode
        data:
          entity_id: fan.getair_comfortcontrol_pro_bt_getair_fan
          preset_mode: Heat Recovery
    - entity: fan.getair_comfortcontrol_pro_bt_getair_fan
      name: Right
      icon: mdi:arrow-right
      show_name: true
      show_state: false
      tap_action:
        action: call-service
        service: fan.set_preset_mode
        data:
          entity_id: fan.getair_comfortcontrol_pro_bt_getair_fan
          preset_mode: "Right (Inverse)"
  bottom:
    - entity: sensor.getair_comfortcontrol_pro_bt_fan_speed
      name: Speed
      show_state: true
      show_name: true
      icon: mdi:fan
    - entity: sensor.getair_comfortcontrol_pro_bt_indoor_temperature
      show_state: true
      show_name: true
      name: Temp
    - entity: sensor.getair_comfortcontrol_pro_bt_indoor_humidity
      show_state: true
      show_name: true
      name: Humidity
```

### Speed scripts (`scripts.yaml`)

```yaml
getair_speed_increase:
  alias: "getAir Speed +"
  sequence:
    - service: fan.set_percentage
      target:
        entity_id: fan.getair_comfortcontrol_pro_bt_getair_fan
      data:
        percentage: >
          {{ [((state_attr('fan.getair_comfortcontrol_pro_bt_getair_fan', 'percentage') | int) + 13), 100] | min }}

getair_speed_decrease:
  alias: "getAir Speed -"
  sequence:
    - service: fan.set_percentage
      target:
        entity_id: fan.getair_comfortcontrol_pro_bt_getair_fan
      data:
        percentage: >
          {{ [((state_attr('fan.getair_comfortcontrol_pro_bt_getair_fan', 'percentage') | int) - 11), 0] | max }}
```

---

## API Reference

This integration uses the official getAir REST API:

| Endpoint | Description |
|----------|-------------|
| `POST /oauth/token` | Authenticate and obtain access token |
| `GET /api/v1/devices/` | List all devices |
| `GET /api/v1/devices/{id}/services/System` | Read system data |
| `GET /api/v1/devices/{zone}.{id}/services/Zone` | Read zone data |
| `PUT /api/v1/devices/{zone}.{id}/services/Zone` | Set zone properties |

### Ventilation Modes

| HA Name | API Value | Description |
|---------|-----------|-------------|
| Heat Recovery | `ventilate_hr` | Normal ventilation with heat recovery |
| Left (Normal) | `ventilate` | Steady airflow in one direction |
| Right (Inverse) | `ventilate_inv` | Steady airflow in opposite direction |
| Rush HR | `rush_hr` | Boost ventilation with heat recovery |

---

## Troubleshooting

**401 Unauthorized on `/api/v1/devices/`**
- Your account doesn't have API access. Email `info@getair.eu` to request it.

**Device not connected**
- The physical device is offline or disconnected from WiFi. Check the getAir app.

**Token expired**
- The integration handles this automatically. If issues persist, reload the integration.

---

## Credits

- getAir REST API documentation: [getaireu/REST-API](https://github.com/getaireu/REST-API)
- Built with ❤️ for the Home Assistant community

---

## License

MIT License — feel free to use, modify and share.
