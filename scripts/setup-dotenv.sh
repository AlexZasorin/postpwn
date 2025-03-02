#!/usr/bin/env zsh

# default settings
####################################

TODOIST_USER_TOKEN=""
RETRY_ATTEMPTS=10

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

TODOIST_USER_TOKEN=$TODOIST_USER_TOKEN
RETRY_ATTEMPTS=$RETRY_ATTEMPTS

EOF

