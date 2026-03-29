/*
 * Filesystem introspection via lstat(2) — symlink awareness for agent hooks.
 */
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>

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

int sentinel_move_replace(const char *src, const char *dst) {
  if (!src || !dst) {
    errno = EINVAL;
    return -1;
  }
  return rename(src, dst);
}

int sentinel_unlink_path(const char *path) {
  if (!path) {
    errno = EINVAL;
    return -1;
  }
  return unlink(path);
}

int sentinel_write_file(const char *path, const unsigned char *data, size_t len, int mode) {
  int fd;
  size_t off = 0;
  ssize_t w;
  if (!path) {
    errno = EINVAL;
    return -1;
  }
  fd = open(path, O_WRONLY | O_CREAT | O_TRUNC, (mode_t)(mode > 0 ? mode : 0644));
  if (fd < 0) {
    return -1;
  }
  while (off < len) {
    w = write(fd, data + off, len - off);
    if (w < 0) {
      if (errno == EINTR) {
        continue;
      }
      (void)close(fd);
      return -1;
    }
    off += (size_t)w;
  }
  (void)fsync(fd);
  if (close(fd) != 0) {
    return -1;
  }
  return 0;
}
