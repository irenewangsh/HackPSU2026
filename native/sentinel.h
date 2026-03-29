/*
 * SentinelOS native API — POSIX systems layer for policy + sandboxed execution.
 */
#ifndef SENTINEL_H
#define SENTINEL_H

#include <stddef.h>
#include <stdint.h>

#ifdef __cplusplus
extern "C" {
#endif

uint64_t sentinel_hash64(const unsigned char *data, size_t len);
int sentinel_hash_chain_hex(const char *prev_hex, const char *entry,
                            char *out_hex, size_t out_hex_len);
int sentinel_hmac_sha256(const unsigned char *key, size_t key_len,
                         const unsigned char *msg, size_t msg_len,
                         unsigned char *out32, size_t out_len);
int sentinel_capability_guard(uint64_t now_epoch, uint64_t exp_epoch,
                              const char *scopes_csv, const char *required_scope);
int sentinel_realpath(const char *path, char *out, size_t outlen);
int sentinel_within_root(const char *canon, const char *root);

/* lstat(2) wrapper: mode = st_mode bits, is_symlink 0/1 */
int sentinel_lstat_info(const char *path, unsigned int *mode_out, int *is_symlink_out);
int sentinel_move_replace(const char *src, const char *dst);
int sentinel_unlink_path(const char *path);
int sentinel_write_file(const char *path, const unsigned char *data, size_t len, int mode);

/*
 * Resolve argv[0] when it is a bare name: searches only /usr/bin, /bin, /usr/sbin, /sbin.
 * Returns 0 on success (full path written).
 */
int sentinel_resolve_binary(const char *name, char *out, size_t outlen);

/*
 * Sandboxed subprocess: chdir(cwd), minimal environ, CPU limit, stdout/stderr captured.
 * argv is a NULL-terminated array (standard execve form). argv[0] may be bare name or path.
 * Buffers are always NUL-terminated when cap > 0.
 */
int sentinel_sandbox_exec(const char *cwd, char *const argv[], char *stdout_out,
                          size_t stdout_cap, char *stderr_out, size_t stderr_cap,
                          int *exit_code_out, unsigned int timeout_sec);
int sentinel_namespace_exec(const char *cwd, char *const argv[], int *exit_code_out,
                            unsigned int timeout_sec);

#ifdef __cplusplus
}
#endif

#endif
