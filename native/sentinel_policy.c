/*
 * SentinelOS — OS-facing policy helpers (POSIX).
 * Used for realpath canonicalization, sandbox prefix checks, and policy digests.
 * Build: make -C native
 */
#include <errno.h>
#include <limits.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#ifdef __APPLE__
#include <CommonCrypto/CommonHMAC.h>
#endif

#include "sentinel.h"

#ifndef PATH_MAX
#define PATH_MAX 4096
#endif

/* FNV-1a 64-bit — stable digest for capability / policy binding */
static uint64_t fnv1a64_update(uint64_t h, const uint8_t *data, size_t len) {
  size_t i;
  for (i = 0; i < len; i++) {
    h ^= (uint64_t)data[i];
    h *= 1099511628211ULL;
  }
  return h;
}

uint64_t sentinel_hash64(const unsigned char *data, size_t len) {
  return fnv1a64_update(14695981039346656037ULL, data, len);
}

/*
 * Build append-only chain digest:
 *   digest = FNV1A64(prev_hex + "\n" + entry)
 * out_hex must have room for at least 17 bytes (16 hex + NUL).
 * Returns 0 on success, -1 on invalid args.
 */
int sentinel_hash_chain_hex(const char *prev_hex, const char *entry,
                            char *out_hex, size_t out_hex_len) {
  uint64_t h = 14695981039346656037ULL;
  size_t n;
  if (!entry || !out_hex || out_hex_len < 17) {
    errno = EINVAL;
    return -1;
  }
  if (!prev_hex) {
    prev_hex = "0000000000000000";
  }
  n = strlen(prev_hex);
  h = fnv1a64_update(h, (const uint8_t *)prev_hex, n);
  h = fnv1a64_update(h, (const uint8_t *)"\n", 1);
  n = strlen(entry);
  h = fnv1a64_update(h, (const uint8_t *)entry, n);
  snprintf(out_hex, out_hex_len, "%016llx", (unsigned long long)h);
  return 0;
}

int sentinel_capability_guard(uint64_t now_epoch, uint64_t exp_epoch,
                              const char *scopes_csv, const char *required_scope) {
  const char *p;
  char req_prefix[128];
  size_t req_len;
  if (!required_scope) {
    errno = EINVAL;
    return 0;
  }
  if (exp_epoch < now_epoch) {
    return 0;
  }
  if (!scopes_csv) {
    return 0;
  }
  if (strcmp(required_scope, "*") == 0) {
    return 1;
  }

  p = strchr(required_scope, ':');
  req_len = p ? (size_t)(p - required_scope) : strlen(required_scope);
  if (req_len >= sizeof(req_prefix)) {
    req_len = sizeof(req_prefix) - 1;
  }
  memcpy(req_prefix, required_scope, req_len);
  req_prefix[req_len] = '\0';

  {
    const char *s = scopes_csv;
    while (*s) {
      const char *e = strchr(s, ',');
      size_t n = e ? (size_t)(e - s) : strlen(s);
      if (n == 1 && s[0] == '*') {
        return 1;
      }
      if (strncmp(s, required_scope, n) == 0 && required_scope[n] == '\0') {
        return 1;
      }
      if (n > req_len + 1 && strncmp(s, req_prefix, req_len) == 0 && s[req_len] == ':') {
        return 1;
      }
      if (!e) {
        break;
      }
      s = e + 1;
      while (*s == ' ') {
        s++;
      }
    }
  }
  return 0;
}

int sentinel_hmac_sha256(const unsigned char *key, size_t key_len,
                         const unsigned char *msg, size_t msg_len,
                         unsigned char *out32, size_t out_len) {
  if (!key || !msg || !out32 || out_len < 32) {
    errno = EINVAL;
    return -1;
  }
#ifdef __APPLE__
  CCHmac(kCCHmacAlgSHA256, key, key_len, msg, msg_len, out32);
  return 0;
#else
  errno = ENOTSUP;
  return -1;
#endif
}

/*
 * Canonicalize path using realpath(3). Returns 0 on success, -1 on error.
 * Writes NUL-terminated path into out (size outlen).
 */
int sentinel_realpath(const char *path, char *out, size_t outlen) {
  char buf[PATH_MAX];
  char *rp;
  size_t n;

  if (!path || !out || outlen == 0) {
    errno = EINVAL;
    return -1;
  }

  rp = realpath(path, buf);
  if (!rp) {
    return -1;
  }

  n = strlen(rp);
  if (n + 1 > outlen) {
    errno = ENAMETOOLONG;
    return -1;
  }

  memcpy(out, rp, n + 1);
  return 0;
}

/*
 * Return 1 if canon is equal to root or is root + '/' + suffix (prefix containment).
 * Both paths must already be canonical.
 */
int sentinel_within_root(const char *canon, const char *root) {
  size_t lc, lr;
  if (!canon || !root) {
    return 0;
  }
  lc = strlen(canon);
  lr = strlen(root);
  if (lr == 0) {
    return 0;
  }
  if (strcmp(canon, root) == 0) {
    return 1;
  }
  if (lc <= lr) {
    return 0;
  }
  if (strncmp(canon, root, lr) != 0) {
    return 0;
  }
  /* require boundary at directory separator */
  if (canon[lr] != '/') {
    return 0;
  }
  return 1;
}
