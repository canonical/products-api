#!/usr/bin/env bash
# Part 2 of the PS7 deploy: log in to JAAS, deploy or refresh the charm, and
# wait until every unit runs the new revision.
#
# Run by action.yaml as a child process of the step shell. It inherits the
# JAAS credentials (JUJU_CLIENT_ID/SECRET) and JUJU_DATA through the
# environment; the parent step removes both when this script finishes.
#
# Expects in the environment:
#   JUJU_CLIENT_ID, JUJU_CLIENT_SECRET, JUJU_DATA,
#   JUJU_CONTROLLER_ADDRESS, JUJU_CONTROLLER_NAME, JUJU_MODEL_NAME,
#   APP_NAME, IMAGE_URL, WAIT_TIMEOUT
set -euo pipefail

POLL_INTERVAL_SECONDS=10

# --- helpers ---------------------------------------------------------------

# Status JSON of just this application.
app_status() {
  juju status "$APP_NAME" --format=json \
    | jq --arg app "$APP_NAME" '.applications[$app]'
}

charm_rev() {
  app_status | jq -er '."charm-rev"'
}

# "900s" / "20m" / "1h" / "900" -> seconds
to_seconds() {
  case "$1" in
    *h) echo $(( ${1%h} * 3600 )) ;;
    *m) echo $(( ${1%m} * 60 )) ;;
    *s) echo "${1%s}" ;;
    *)  echo "$1" ;;
  esac
}

# --- steps -----------------------------------------------------------------

login_and_switch_model() {
  echo "::group::Log in to JAAS"
  juju login "$JUJU_CONTROLLER_ADDRESS" -c "$JUJU_CONTROLLER_NAME"

  local full_model
  full_model=$(juju models -c "$JUJU_CONTROLLER_NAME" --format json \
    | jq -r --arg model "$JUJU_MODEL_NAME" '.models[] | select(."short-name" == $model) | .name' \
    | head -n1)
  if [ -z "$full_model" ]; then
    echo "::error::Model '$JUJU_MODEL_NAME' not found on controller '$JUJU_CONTROLLER_NAME'."
    exit 1
  fi
  juju switch "$JUJU_CONTROLLER_NAME:${full_model}"
  echo "::endgroup::"
}

# Deploys or refreshes the charm and sets EXPECTED_CHARM_REV.
deploy_or_refresh() {
  echo "::group::Deploy charm"
  shopt -s nullglob
  local charms=(./*.charm)
  shopt -u nullglob
  if [ "${#charms[@]}" -ne 1 ]; then
    echo "::error::Expected exactly one .charm file, found ${#charms[@]}: ${charms[*]:-none}"
    exit 1
  fi
  local charm_file="${charms[0]}"

  local model_status
  if ! model_status=$(juju status --format=json); then
    echo "::error::Could not read the status of model '$JUJU_MODEL_NAME' (see the Juju error above); not deploying."
    exit 1
  fi

  if jq -e --arg app "$APP_NAME" '(.applications // {}) | has($app)' <<<"$model_status" >/dev/null; then
    local previous_rev
    previous_rev=$(charm_rev)
    echo "Refreshing $APP_NAME (currently charm revision $previous_rev)"
    juju refresh "$APP_NAME" --path="$charm_file" --resource flask-app-image="$IMAGE_URL"
    EXPECTED_CHARM_REV=$(charm_rev)
    if [ "$EXPECTED_CHARM_REV" = "$previous_rev" ]; then
      echo "::error::Juju did not select a new charm revision for $APP_NAME."
      exit 1
    fi
  else
    echo "Deploying $APP_NAME"
    juju deploy "$charm_file" "$APP_NAME" --resource flask-app-image="$IMAGE_URL"
    EXPECTED_CHARM_REV=$(charm_rev)
  fi
  echo "Target charm revision: $EXPECTED_CHARM_REV"
  echo "::endgroup::"
}

# True when the application has all of its expected units, and every unit
# runs EXPECTED_CHARM_REV and is active/idle.
#
# The application's charm-rev is updated as soon as `juju refresh` returns,
# before any unit has upgraded, so an application-level check can pass while
# units still run the old charm/image.
#
# Unit count: `scale` is the number of units the application should have
# (k8s models). Units that are still being created may not be listed yet, so
# "all listed units are healthy" alone could pass with e.g. 1 of 3 units.
# We require the number of listed units to equal `scale`.
#
# Per unit we require:
#   - no `upgrading-from` (set while a unit's charm differs from the
#     application's), i.e. the unit is on EXPECTED_CHARM_REV
#   - workload active and agent idle
# Each --path refresh carries the new image in the same operation, so this
# also covers the image rollout.
rollout_complete() {
  jq -e --argjson rev "$EXPECTED_CHARM_REV" '
      ."charm-rev" == $rev
      and ."application-status".current == "active"
      and (.scale | type) == "number" and .scale > 0
      and ((.units // {}) | length) == .scale
      and all((.units // {})[];
              (has("upgrading-from") | not)
              and ."workload-status".current == "active"
              and ."juju-status".current == "idle")
    ' <<<"$1" >/dev/null
}

print_unit_progress() {
  jq -r '"  units: \((.units // {}) | length)/\(.scale // "unknown scale")"' <<<"$1" 2>/dev/null || true
  jq -r '(.units // {}) | to_entries[] | .key as $unit | .value
         | "  \($unit): workload=\(."workload-status".current) agent=\(."juju-status".current)"
           + (if has("upgrading-from") then " (upgrading from \(."upgrading-from"))" else "" end)' \
    <<<"$1" 2>/dev/null || true
}

# Polls until rollout_complete holds on two consecutive polls (so a brief
# active/idle blip mid-rollout is not mistaken for success) or WAIT_TIMEOUT.
wait_for_rollout() {
  echo "::group::Wait for all units of $APP_NAME to run charm revision $EXPECTED_CHARM_REV"
  local deadline=$(( SECONDS + $(to_seconds "$WAIT_TIMEOUT") ))
  local stable=0 status_json

  while true; do
    status_json=$(app_status)
    if rollout_complete "$status_json"; then
      stable=$(( stable + 1 ))
      if [ "$stable" -ge 2 ]; then
        echo "All units of $APP_NAME are active and idle on charm revision $EXPECTED_CHARM_REV."
        break
      fi
    else
      stable=0
    fi

    if [ "$SECONDS" -ge "$deadline" ]; then
      echo "::error::$APP_NAME did not finish rolling out charm revision $EXPECTED_CHARM_REV within $WAIT_TIMEOUT"
      juju status "$APP_NAME" || true
      exit 1
    fi

    print_unit_progress "$status_json"
    sleep "$POLL_INTERVAL_SECONDS"
  done
  echo "::endgroup::"
}

# --- main ------------------------------------------------------------------

login_and_switch_model
deploy_or_refresh
wait_for_rollout
