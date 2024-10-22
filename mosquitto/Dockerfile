FROM eclipse-mosquitto:2.0.18

COPY ./users /mosquitto/config/users

COPY mosquitto.conf /mosquitto/config/mosquitto.conf
COPY entrypoint.sh /

ENTRYPOINT ["sh", "./entrypoint.sh"]

CMD ["/usr/sbin/mosquitto", "-c", "/mosquitto/config/mosquitto.conf"]