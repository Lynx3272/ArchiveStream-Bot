package com.archivestream

import com.lagradost.cloudstream3.plugins.BasePlugin
import com.lagradost.cloudstream3.plugins.CloudstreamPlugin

@CloudstreamPlugin
class ArchiveStreamPlugin : BasePlugin() {
    override fun load() {
        // Tum provider'lar bu sekilde kaydedilir.
        registerMainAPI(ArchiveStreamProvider())
    }
}
