#ifndef FINDUAS_IDENTITY_TEST_HOOKS_H
#define FINDUAS_IDENTITY_TEST_HOOKS_H

/* Read platform declarations before substitution (including Darwin aliases). */
#include <fcntl.h>
#include <stddef.h>
#include <sys/types.h>
#include <unistd.h>

int finduas_test_open(const char *path, int flags, ...);
ssize_t finduas_test_read(int fd, void *buffer, size_t count);
int finduas_test_close(int fd);
pid_t finduas_test_getpid(void);
uid_t finduas_test_getuid(void);
gid_t finduas_test_getgid(void);

#define open finduas_test_open
#define read finduas_test_read
#define close finduas_test_close
#define getpid finduas_test_getpid
#define getuid finduas_test_getuid
#define getgid finduas_test_getgid
#endif
