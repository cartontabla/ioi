import paho.mqtt.client as mqtt

class MQTTClient:
    def __init__(self, host='localhost', port=1883, client_id='smartcam'):
        self.host = host
        self.port = port
        self.client = mqtt.Client(client_id=client_id)

    def connect(self):
        try:
            self.client.connect(self.host, self.port, keepalive=60)
            self.client.loop_start()
        except Exception as e:
            print('MQTT connect error:', e)

    def publish(self, topic, payload, qos=0, retain=False):
        try:
            self.client.publish(topic, payload, qos=qos, retain=retain)
        except Exception as e:
            print('MQTT publish error:', e)

    def subscribe(self, topic, callback=None):
        if callback:
            self.client.message_callback_add(topic, lambda client, userdata, msg: callback(msg.topic, msg.payload))
        self.client.subscribe(topic)
