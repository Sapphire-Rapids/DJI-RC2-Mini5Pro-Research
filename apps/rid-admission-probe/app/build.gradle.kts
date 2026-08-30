plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.finduas.ridobserver"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.finduas.ridobserver"
        minSdk = 29
        targetSdk = 35
        versionCode = 11
        versionName = "0.11.0-report-export"
    }

    // v0.11 is intentionally built from a separate, minimal source set. The withdrawn
    // localhost observer is not distributed in this repository. A connection to DJI's
    // single-client broker can evict DJI Fly even when the socket is input-only.
    sourceSets {
        getByName("main") {
            manifest.srcFile("src/safe/AndroidManifest.xml")
            java.setSrcDirs(listOf("src/safe/java"))
            res.setSrcDirs(listOf("src/safe/res"))
        }
        getByName("test") {
            java.setSrcDirs(listOf("src/safeTest/java"))
        }
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }

    kotlinOptions {
        jvmTarget = "17"
    }
}

dependencies {
    testImplementation("junit:junit:4.13.2")
}
