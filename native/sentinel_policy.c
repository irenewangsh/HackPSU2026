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
