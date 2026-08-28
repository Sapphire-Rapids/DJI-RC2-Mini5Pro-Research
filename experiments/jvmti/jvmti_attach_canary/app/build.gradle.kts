plugins {
    id("com.android.application")
}

android {
    namespace = "com.finduas.jvmti.canary.carrier"
    compileSdk = 35
    ndkVersion = "27.2.12479018"

    defaultConfig {
        applicationId = "com.finduas.jvmti.canary.carrier"
        minSdk = 30
        targetSdk = 30
        versionCode = 1
        versionName = "0.1.0-research"

        ndk {
            abiFilters += setOf("arm64-v8a")
        }

        externalNativeBuild {
            cmake {
                arguments += listOf("-DANDROID_STL=none")
            }
        }
    }

    buildTypes {
        debug {
            isDebuggable = true
            isMinifyEnabled = false
        }
    }

    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }

    packaging {
        jniLibs {
            // Keep the .so compressed in the APK so Package Manager extracts a
            // standalone file into nativeLibraryDir on Android 11.
            useLegacyPackaging = true
        }
    }

    buildFeatures {
        buildConfig = false
    }
}
