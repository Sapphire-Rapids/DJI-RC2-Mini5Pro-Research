plugins {
    id("com.android.application")
}

android {
    namespace = "com.finduas.rc2ridadmin"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.finduas.rc2ridadmin"
        minSdk = 29
        targetSdk = 29
        versionCode = 14
        versionName = "0.8.1-identity-safety-locked"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }

    lint {
        // This laboratory APK deliberately targets the RC 2's Android 11
        // hidden-API compatibility level and is not a Google Play artifact.
        disable += "ExpiredTargetSdkVersion"
    }
}

dependencies {
    testImplementation("junit:junit:4.13.2")
}
