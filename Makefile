SERVICE := interstellar-mission-control

DESTDIR ?= dist_root
SERVICEDIR ?= /srv/$(SERVICE)

.PHONY: build install


build:
	echo "Nothing to build"


install: build
	mkdir -p $(DESTDIR)$(SERVICEDIR)/
	mkdir -p $(DESTDIR)$(SERVICEDIR)/imc/
	cp -r imc/* $(DESTDIR)$(SERVICEDIR)/imc/
	rm $(DESTDIR)$(SERVICEDIR)/imc/Dockerfile.deps
	yq -y 'del(.services."imc_deps")' docker-compose.yml > $(DESTDIR)$(SERVICEDIR)/docker-compose.yml
	mkdir -p $(DESTDIR)/etc/systemd/system/faustctf.target.wants/
	ln -s /etc/systemd/system/docker-compose@.service $(DESTDIR)/etc/systemd/system/faustctf.target.wants/docker-compose@$(SERVICE).service
