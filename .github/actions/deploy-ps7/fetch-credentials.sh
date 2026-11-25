# Part 1 of the PS7 deploy: fetch the JAAS service-account credentials from
# Vault, then revoke the Vault token straight away.
#
# This file is SOURCED (not executed) by action.yaml, so the credentials stay
# in the calling shell's memory only: they are never written to step outputs,
# $GITHUB_ENV or disk.
#
# Expects in the environment:
#   VAULT_ADDR, VAULT_ROLE_ID, VAULT_SECRET_ID, VAULT_MOUNT, VAULT_CREDENTIALS_PATH
# Exports on success:
#   JUJU_CLIENT_ID, JUJU_CLIENT_SECRET (read by `juju login` and every juju command)

# Revoke the Vault token if one is held. Safe to call more than once; also
# called from the step's EXIT trap.
revoke_vault_token() {
  if [ -z "${VAULT_TOKEN:-}" ]; then
    return 0
  fi
  if vault token revoke -self >/dev/null 2>&1; then
    echo "Vault token revoked."
    unset VAULT_TOKEN
  else
    echo "::error::Failed to revoke Vault token."
    unset VAULT_TOKEN
    return 1
  fi
}

fetch_jaas_credentials() {
  echo "::group::Fetch JAAS credentials from Vault"
  echo "::add-mask::$VAULT_ROLE_ID"
  echo "::add-mask::$VAULT_SECRET_ID"

  VAULT_TOKEN=$(vault write -field=token auth/approle/login \
    role_id="$VAULT_ROLE_ID" \
    secret_id="$VAULT_SECRET_ID")
  echo "::add-mask::$VAULT_TOKEN"
  export VAULT_TOKEN
  unset VAULT_ROLE_ID VAULT_SECRET_ID

  # Pass the mount explicitly: without -mount, `vault kv get` first looks the
  # mount up from the full path (sys/internal/ui/mounts/<path>), which the
  # AppRole policy does not allow (403).
  # One request; the JSON (with secrets) only ever lives in this variable.
  local creds_json
  creds_json=$(vault kv get -format=json -mount="$VAULT_MOUNT" "$VAULT_CREDENTIALS_PATH")
  JUJU_CLIENT_ID=$(jq -er '.data.data.juju_client_id' <<<"$creds_json")
  echo "::add-mask::$JUJU_CLIENT_ID"
  JUJU_CLIENT_SECRET=$(jq -er '.data.data.juju_client_secret' <<<"$creds_json")
  echo "::add-mask::$JUJU_CLIENT_SECRET"
  unset creds_json
  export JUJU_CLIENT_ID JUJU_CLIENT_SECRET

  # The token is no longer needed once the credentials are read.
  revoke_vault_token
  echo "::endgroup::"
}
