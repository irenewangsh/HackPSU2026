# macOS: libsentinel.dylib | Linux: libsentinel.so
UNAME := $(shell uname -s)
SRCS := sentinel_policy.c sentinel_fs.c sentinel_exec.c

ifeq ($(UNAME),Darwin)
  LIB := libsentinel.dylib
  CFLAGS += -fPIC -Wall -Wextra -O2 -std=c11
  LDFLAGS += -dynamiclib
else
  LIB := libsentinel.so
  CFLAGS += -fPIC -Wall -Wextra -O2 -std=c11 -shared
endif

all: $(LIB)

$(LIB): $(SRCS) sentinel.h
ifeq ($(UNAME),Darwin)
	$(CC) $(CFLAGS) -o $(LIB) $(SRCS) $(LDFLAGS)
else
	$(CC) $(CFLAGS) -o $(LIB) $(SRCS)
endif

clean:
	rm -f $(LIB)

.PHONY: all clean
