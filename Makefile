all: install systemd config

install:
	pip install .

systemd:
	cp misc/rpi_measure.service /etc/systemd/system/

config:
	cp rpi_measure/measure.conf.template /etc/rpi_measure.conf
