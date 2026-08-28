plugins {
    id("com.android.application")
}

android {
    namespace = "com.finduas.rc2settingslauncher"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.finduas.rc2settingslauncher"
        minSdk = 29
        targetSdk = 35
        versionCode = 1
        versionName = "1.0.0"
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

    packaging {
        resources.excludes += setOf(
            "META-INF/DEPENDENCIES",
            "META-INF/LICENSE*",
            "META-INF/NOTICE*"
        )
    }
}

dependencies {
    testImplementation("junit:junit:4.13.2")
}
