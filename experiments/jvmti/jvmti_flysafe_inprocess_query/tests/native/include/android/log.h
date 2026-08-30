#ifndef FINDUAS_HOST_ANDROID_LOG_H
#define FINDUAS_HOST_ANDROID_LOG_H

#define ANDROID_LOG_INFO 4

int __android_log_print(int priority, const char *tag, const char *format, ...)
    __attribute__((format(printf, 3, 4)));

#endif
