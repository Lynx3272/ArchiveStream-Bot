rootProject.name = "CloudstreamPlugins"

// Bu dosya hangi projelerin dahil edilecegini belirler.
// build.gradle.kts iceren tum klasorler otomatik dahil edilir.

val disabled = listOf<String>()

File(rootDir, ".").eachDir { dir ->
    if (!disabled.contains(dir.name) && File(dir, "build.gradle.kts").exists()) {
        include(dir.name)
    }
}

fun File.eachDir(block: (File) -> Unit) {
    listFiles()?.filter { it.isDirectory }?.forEach { block(it) }
}
