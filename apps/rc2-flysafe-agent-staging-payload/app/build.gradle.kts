plugins {
    id("com.android.application")
}

android {
    namespace = "com.finduas.rc2flysafeagentpayload"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.finduas.rc2flysafeagentpayload"
        minSdk = 30
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0-emulator-observed"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    sourceSets {
        getByName("main").jniLibs.srcDir(layout.buildDirectory.dir("generated/jniLibs"))
    }

    packaging {
        jniLibs.useLegacyPackaging = false
    }
}
