#!/usr/bin/env zsh

# default settings
####################################

TODOIST_CLIENTID=""
TODOIST_API_KEY=""
TODOIST_USER_TOKEN=""

# direnv
####################################
cat <<EOF > .envrc

source ./.venv/bin/activate

EOF

# overrides
####################################
DOTENV_OVERRIDES=$(dirname $0)/.env
if [ -f $DOTENV_OVERRIDES ]; then
  echo "Sourcing overrides from $DOTENV_OVERRIDES"
  source $DOTENV_OVERRIDES
fi

# project
####################################
cat <<EOF > .env

TODOIST_CLIENTID=$TODOIST_CLIENTID
TODOIST_API_KEY=$TODOIST_TOKEN
TODOIST_USER_TOKEN=$TODOIST_USER_TOKEN

EOF

