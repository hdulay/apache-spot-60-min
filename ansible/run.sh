#!/bin/bash
export ANSIBLE_HOST_KEY_CHECKING=False
ansible-playbook  --private-key $PEM spot-playbook.yml -i inventory.ini