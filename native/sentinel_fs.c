/*
 * Filesystem introspection via lstat(2) — symlink awareness for agent hooks.
 */
#include <errno.h>
#include <sys/stat.h>

#include "sentinel.h"

int sentinel_lstat_info(const char *path, unsigned int *mode_out, int *is_symlink_out) {
  struct stat st;

  if (!path || !mode_out || !is_symlink_out) {
    errno = EINVAL;
    return -1;
  }

  if (lstat(path, &st) != 0) {
    return -1;
  }

  *mode_out = (unsigned int)st.st_mode;
  *is_symlink_out = S_ISLNK(st.st_mode) ? 1 : 0;
  return 0;
}
