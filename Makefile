all: deps

install: systemd config
	sudo pip install .

deps:
	pip install -r requirements.txt

systemd:
	sudo cp misc/rpi_measure.service /etc/systemd/system/

config:
ifeq ("$(wildcard /etc/rpi_measure/rpi_measure.conf)","")
	sudo mkdir -p /etc/rpi_measure/cert
	sudo cp rpi_measure/rpi_measure.conf.template /etc/rpi_measure/rpi_measure.conf
	sudo chmod 0700 /etc/rpi_measure/cert
endif

