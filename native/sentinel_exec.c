/*
 * Sandboxed child: fork(2), pipe(2), execve(2), minimal environment, RLIMIT_CPU.
 */
#include <errno.h>
#include <limits.h>
#include <poll.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/resource.h>
#include <sys/wait.h>
#include <unistd.h>

#include "sentinel.h"

#ifdef __linux__
#include <sched.h>
#endif

#ifndef PATH_MAX
#define PATH_MAX 4096
#endif

#ifndef STDERR_FILENO
#define STDERR_FILENO 2
#endif
#ifndef STDOUT_FILENO
#define STDOUT_FILENO 1
#endif

static ssize_t append_buf(char *dst, size_t cap, size_t *used, const char *src, size_t n) {
  size_t u;
  size_t room;
  if (!dst || cap == 0) {
    return -1;
  }
  u = *used;
  room = (u < cap - 1) ? (cap - 1 - u) : 0;
  if (n > room) {
    n = room;
  }
  if (n > 0) {
    memcpy(dst + u, src, n);
    u += n;
    dst[u] = '\0';
    *used = u;
  }
  return (ssize_t)n;
}

int sentinel_resolve_binary(const char *name, char *out, size_t outlen) {
  size_t i;
  if (!name || !out || outlen == 0) {
    errno = EINVAL;
    return -1;
  }
  if (strchr(name, '/') != NULL) {
    if (sentinel_realpath(name, out, outlen) != 0) {
      return -1;
    }
    if (access(out, X_OK) != 0) {
      return -1;
    }
    return 0;
  }
  {
    static const char *dirs[] = {"/usr/bin/", "/bin/", "/usr/sbin/", "/sbin/"};
    for (i = 0; i < sizeof(dirs) / sizeof(dirs[0]); i++) {
      char trial[PATH_MAX];
      size_t dl = strlen(dirs[i]);
      size_t nl = strlen(name);
      if (dl + nl + 1 > sizeof(trial)) {
        errno = ENAMETOOLONG;
        return -1;
      }
      memcpy(trial, dirs[i], dl);
      memcpy(trial + dl, name, nl + 1);
      if (access(trial, X_OK) == 0) {
        if (strlen(trial) + 1 > outlen) {
          errno = ENAMETOOLONG;
          return -1;
        }
        memcpy(out, trial, strlen(trial) + 1);
        return 0;
      }
    }
  }
  errno = ENOENT;
  return -1;
}

int sentinel_sandbox_exec(const char *cwd, char *const argv[], char *stdout_out,
                          size_t stdout_cap, char *stderr_out, size_t stderr_cap,
                          int *exit_code_out, unsigned int timeout_sec) {
  int po[2] = {-1, -1};
  int pe[2] = {-1, -1};
  pid_t pid;
  char binpath[PATH_MAX];
  char *child_argv[256];
  int st = 0;
  size_t out_u = 0;
  size_t err_u = 0;
  int i;
  int argc;

  if (!cwd || !argv || !argv[0] || !exit_code_out) {
    errno = EINVAL;
    return -1;
  }
  if (stdout_out && stdout_cap > 0) {
    stdout_out[0] = '\0';
  }
  if (stderr_out && stderr_cap > 0) {
    stderr_out[0] = '\0';
  }
  *exit_code_out = -1;

  if (sentinel_resolve_binary(argv[0], binpath, sizeof(binpath)) != 0) {
    return -1;
  }

  argc = 0;
  while (argv[argc] && argc < (int)(sizeof(child_argv) / sizeof(child_argv[0]) - 1)) {
    argc++;
  }
  if (argc == 0 || argc >= (int)(sizeof(child_argv) / sizeof(child_argv[0]) - 1)) {
    errno = E2BIG;
    return -1;
  }

  for (i = 0; i < argc; i++) {
    child_argv[i] = (i == 0) ? binpath : argv[i];
  }
  child_argv[argc] = NULL;

  if (pipe(po) != 0 || pipe(pe) != 0) {
    if (po[0] >= 0) {
      close(po[0]);
    }
    if (po[1] >= 0) {
      close(po[1]);
    }
    if (pe[0] >= 0) {
      close(pe[0]);
    }
    if (pe[1] >= 0) {
      close(pe[1]);
    }
    return -1;
  }

  pid = fork();
  if (pid < 0) {
    close(po[0]);
    close(po[1]);
    close(pe[0]);
    close(pe[1]);
    return -1;
  }

  if (pid == 0) {
    char *env[] = {"SENTINEL_SANDBOX=1", "PATH=/usr/bin:/bin:/usr/sbin:/sbin", NULL};
    struct rlimit rl_cpu;

    (void)signal(SIGPIPE, SIG_DFL);
    if (timeout_sec > 0) {
      rl_cpu.rlim_cur = (rlim_t)timeout_sec;
      rl_cpu.rlim_max = (rlim_t)timeout_sec;
      (void)setrlimit(RLIMIT_CPU, &rl_cpu);
    }
    if (chdir(cwd) != 0) {
      _exit(126);
    }
    (void)dup2(po[1], STDOUT_FILENO);
    (void)dup2(pe[1], STDERR_FILENO);
    close(po[0]);
    close(po[1]);
    close(pe[0]);
    close(pe[1]);
    (void)execve(binpath, child_argv, env);
    _exit(127);
  }

  close(po[1]);
  close(pe[1]);
  po[1] = -1;
  pe[1] = -1;

  {
    int remaining_ms = (timeout_sec > 0 ? (int)timeout_sec * 1000 : 8000);
    int child_done = 0;

    while (1) {
      struct pollfd fds[2];
      int nf = 0;
      int pr;
      char chunk[4096];
      ssize_t nr;
      pid_t w;

      if (po[0] >= 0) {
        fds[nf].fd = po[0];
        fds[nf].events = POLLIN;
        nf++;
      }
      if (pe[0] >= 0) {
        fds[nf].fd = pe[0];
        fds[nf].events = POLLIN;
        nf++;
      }

      pr = poll(fds, (unsigned int)nf, nf > 0 ? 200 : 0);
      if (pr < 0 && errno != EINTR) {
        break;
      }

      if (pr > 0) {
        for (i = 0; i < nf; i++) {
          if (!(fds[i].revents & (POLLIN | POLLHUP))) {
            continue;
          }
          nr = read(fds[i].fd, chunk, sizeof(chunk));
          if (nr > 0) {
            if (fds[i].fd == po[0] && stdout_out) {
              (void)append_buf(stdout_out, stdout_cap, &out_u, chunk, (size_t)nr);
            } else if (fds[i].fd == pe[0] && stderr_out) {
              (void)append_buf(stderr_out, stderr_cap, &err_u, chunk, (size_t)nr);
            }
          } else if (nr == 0) {
            if (fds[i].fd == po[0]) {
              close(po[0]);
              po[0] = -1;
            } else {
              close(pe[0]);
              pe[0] = -1;
            }
          }
        }
      } else if (pr == 0) {
        remaining_ms -= 200;
        if (!child_done && remaining_ms <= 0) {
          (void)kill(pid, SIGKILL);
        }
      }

      w = waitpid(pid, &st, WNOHANG);
      if (w == pid) {
        child_done = 1;
      }

      if (child_done && po[0] < 0 && pe[0] < 0) {
        break;
      }
      if (child_done && pr == 0 && po[0] < 0 && pe[0] < 0) {
        break;
      }
    }

    if (!child_done) {
      (void)waitpid(pid, &st, 0);
    } else {
      (void)waitpid(pid, &st, 0);
    }
  }

  if (po[0] >= 0) {
    close(po[0]);
  }
  if (pe[0] >= 0) {
    close(pe[0]);
  }

  if (WIFEXITED(st)) {
    *exit_code_out = WEXITSTATUS(st);
  } else if (WIFSIGNALED(st)) {
    *exit_code_out = 128 + WTERMSIG(st);
  } else {
    *exit_code_out = -1;
  }
  return 0;
}

int sentinel_namespace_exec(const char *cwd, char *const argv[], int *exit_code_out,
                            unsigned int timeout_sec) {
#ifndef __linux__
  (void)cwd;
  (void)argv;
  (void)exit_code_out;
  (void)timeout_sec;
  errno = ENOTSUP;
  return -1;
#else
  pid_t pid;
  int st = 0;
  char binpath[PATH_MAX];
  char *child_argv[256];
  int argc = 0;
  int i;
  int waited_ms = 0;

  if (!cwd || !argv || !argv[0] || !exit_code_out) {
    errno = EINVAL;
    return -1;
  }
  if (sentinel_resolve_binary(argv[0], binpath, sizeof(binpath)) != 0) {
    return -1;
  }
  while (argv[argc] && argc < (int)(sizeof(child_argv) / sizeof(child_argv[0]) - 1)) {
    argc++;
  }
  if (argc == 0 || argc >= (int)(sizeof(child_argv) / sizeof(child_argv[0]) - 1)) {
    errno = E2BIG;
    return -1;
  }
  for (i = 0; i < argc; i++) {
    child_argv[i] = (i == 0) ? binpath : argv[i];
  }
  child_argv[argc] = NULL;

  pid = fork();
  if (pid < 0) {
    return -1;
  }
  if (pid == 0) {
    char *env[] = {"SENTINEL_SANDBOX=1", "PATH=/usr/bin:/bin:/usr/sbin:/sbin", NULL};
    struct rlimit rl_cpu;
    (void)signal(SIGPIPE, SIG_DFL);
    if (timeout_sec > 0) {
      rl_cpu.rlim_cur = (rlim_t)timeout_sec;
      rl_cpu.rlim_max = (rlim_t)timeout_sec;
      (void)setrlimit(RLIMIT_CPU, &rl_cpu);
    }
    /* Best-effort namespace isolation; if unsupported, fail closed in this branch. */
    if (unshare(CLONE_NEWNS | CLONE_NEWUTS | CLONE_NEWIPC | CLONE_NEWNET) != 0) {
      _exit(126);
    }
    if (chdir(cwd) != 0) {
      _exit(126);
    }
    (void)execve(binpath, child_argv, env);
    _exit(127);
  }

  while (1) {
    pid_t w = waitpid(pid, &st, WNOHANG);
    if (w == pid) {
      break;
    }
    if (w < 0 && errno != EINTR) {
      break;
    }
    usleep(100000);
    waited_ms += 100;
    if (timeout_sec > 0 && waited_ms >= (int)timeout_sec * 1000) {
      (void)kill(pid, SIGKILL);
      (void)waitpid(pid, &st, 0);
      break;
    }
  }

  if (WIFEXITED(st)) {
    *exit_code_out = WEXITSTATUS(st);
  } else if (WIFSIGNALED(st)) {
    *exit_code_out = 128 + WTERMSIG(st);
  } else {
    *exit_code_out = -1;
  }
  return 0;
#endif
}
