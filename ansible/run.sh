#!/bin/bash
ansible-playbook  --private-key $PEM spot-playbook.yml -i inventory.ini