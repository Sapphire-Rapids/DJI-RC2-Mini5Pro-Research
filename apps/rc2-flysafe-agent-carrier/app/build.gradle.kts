plugins {
    id("com.android.application")
}

android {
    namespace = "com.finduas.rc2flysafeagentcarrier"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.finduas.rc2flysafeagentcarrier"
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

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }

    sourceSets {
        getByName("main").jniLibs.srcDir(layout.buildDirectory.dir("generated/jniLibs"))
    }

    packaging {
        jniLibs.useLegacyPackaging = true
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
