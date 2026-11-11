plugins {
    id("com.android.application")
}

android {
    namespace = "com.lin4cre.sentinel"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.lin4cre.sentinel"
        minSdk = 26
        targetSdk = 35
        versionCode = 1
        versionName = "0.1.0"
    }

    buildTypes {
        debug {
            applicationIdSuffix = ".preview"
            versionNameSuffix = "-preview"
        }
        release {
            isMinifyEnabled = false
            // Release workflow intentionally publishes an explicitly labelled debug-signed preview APK.
        }
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
}
