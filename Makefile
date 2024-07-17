#
# Xcalibu installation.
#

# Installation directories :
# /users/blissadm/python/bliss_modules/
# /users/blissadm/local/userconf/xcalibu/
# /users/blissadm/local/userconf/xcalibu/templates/
# /users/blissadm/server/src/xcalibu_server


BLISSADM_PATH=/users/blissadm

MOD_PATH=${BLISSADM_PATH}/python/bliss_modules

CONFIG_PATH=${BLISSADM_PATH}/local/userconf/xcalibu

TEMPLATES_PATH=${CONFIG_PATH}/templates

DEV_PATH=${PWD}

# "Distribution" installation.
# Copy of files from current git repository.
install:
        ####  install of the py module.
	pip install .

        ####  config dir and template files.
	mkdir -p ${TEMPLATES_PATH}
	chmod 777 ${CONFIG_PATH}
	cp examples/*.calib ${TEMPLATES_PATH}

        ####  tango server and startup-script
	mkdir -p ${BLISSADM_PATH}/server/src

        # startup script
	cp --backup=simple --suffix=.bup tango/xcalibu_server ${BLISSADM_PATH}/server/src/xcalibu_server

        # tango DS
	cp --backup=simple --suffix=.bup tango/Xcalibuds.py ${BLISSADM_PATH}/server/src/Xcalibuds.py


test:
	@echo "-------------- xcalibu TEST ---------------"
	python xcalibu.py demo

