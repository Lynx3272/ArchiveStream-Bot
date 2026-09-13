package com.archivestream.plugin

import com.lagradost.cloudstream3.*
import com.lagradost.cloudstream3.utils.*
import com.lagradost.cloudstream3.utils.AppUtils.tryParseJson
import java.net.URLEncoder

/**
 * Archive.org (kamu mali / Creative Commons icerik) CloudStream provider'i.
 * Bot tarafindan otomatik uretilmistir - ArchiveOrgProvider.kt
 */
class ArchiveOrgProvider : MainAPI() {
    override var mainUrl = "https://archive.org"
    override var name = "Archive.org (Kamu Mali)"
    override val supportedTypes = setOf(TvType.Movie, TvType.Documentary)
    override var lang = "en"
    override val hasMainPage = true
    override val hasChromecastSupport = true

    private fun searchUrl(query: String, rows: Int = 30): String {
        val q = URLEncoder.encode("mediatype:(movies) AND ($query)", "UTF-8")
        return "$mainUrl/advancedsearch.php?q=$q&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=year&rows=$rows&page=1&output=json"
    }

    private fun collectionUrl(collection: String, rows: Int = 30): String {
        val q = URLEncoder.encode("collection:($collection) AND mediatype:(movies)", "UTF-8")
        return "$mainUrl/advancedsearch.php?q=$q&fl%5B%5D=identifier&fl%5B%5D=title&fl%5B%5D=year&rows=$rows&page=1&output=json&sort%5B%5D=downloads+desc"
    }

    private data class Doc(
        val identifier: String? = null,
        val title: String? = null,
        val year: Any? = null,
    ) {
        fun yearStr(): String = when (year) {
            is List<*> -> year.firstOrNull()?.toString() ?: ""
            else -> year?.toString() ?: ""
        }
    }

    private data class SearchResponseJson(val response: ResponseJson? = null)
    private data class ResponseJson(val docs: List<Doc> = emptyList())

    private fun docToSearchResponse(doc: Doc): SearchResponse? {
        val id = doc.identifier ?: return null
        val title = doc.title ?: id
        val year = doc.yearStr().toIntOrNull()
        return MovieSearchResponse(title, "$mainUrl/details/$id", this.name, TvType.Movie, "$mainUrl/details/$id", year)
    }

    override val mainPage = mainPageOf(
        "feature_films" to "Kamu Mali Filmler",
        "Film_Noir" to "Film Noir",
        "SciFi_Horror" to "Sci-Fi / Horror",
        "classiccartoons" to "Klasik Cizgi Filmler",
        "prelinger" to "Prelinger Arsivi",
        "nasa" to "NASA",
    )

    override suspend fun getMainPage(page: Int, request: MainPageRequest): HomePageResponse {
        val res = app.get(collectionUrl(request.data)).parsed<SearchResponseJson>()
        val items = res.response?.docs?.mapNotNull { docToSearchResponse(it) } ?: emptyList()
        return newHomePageResponse(request.name, items)
    }

    override suspend fun search(query: String): List<SearchResponse> {
        val res = app.get(searchUrl(query)).parsed<SearchResponseJson>()
        return res.response?.docs?.mapNotNull { docToSearchResponse(it) } ?: emptyList()
    }

    private data class MetaFile(
        val name: String? = null,
        val format: String? = null,
        val size: String? = null,
    )

    private data class MetaJson(
        val metadata: MetaData? = null,
        val files: List<MetaFile> = emptyList(),
        val server: String? = null,
        val dir: String? = null,
    )

    private data class MetaData(
        val title: String? = null,
        val description: String? = null,
        val year: Any? = null,
        val runtime: Any? = null,
    )

    override suspend fun load(url: String): LoadResponse {
        val identifier = url.substringAfterLast("/details/")
        val meta = app.get("$mainUrl/metadata/$identifier").parsed<MetaJson>()
        val md = meta.metadata
        val title = md?.title ?: identifier
        val year = when (val y = md?.year) {
            is List<*> -> y.firstOrNull()?.toString()?.toIntOrNull()
            else -> y?.toString()?.toIntOrNull()
        }
        val plot = md?.description?.let { d -> if (d is List<*>) d.firstOrNull()?.toString() else d.toString() }
        return newMovieLoadResponse(
            title,
            url,
            TvType.Movie,
            identifier,
        ) {
            this.year = year
            this.plot = plot
            this.posterUrl = "$mainUrl/thumbs/$identifier/__ia_thumb.jpg"
        }
    }

    override suspend fun loadLinks(
        data: String,
        isCasting: Boolean,
        subtitleCallback: (SubtitleFile) -> Unit,
        callback: (ExtractorLink) -> Unit
    ): Boolean {
        val meta = app.get("$mainUrl/metadata/$data").parsed<MetaJson>()
        val server = meta.server ?: "https://archive.org"
        val dir = meta.dir ?: "/download/$data"
        var found = false
        for (file in meta.files) {
            val name = file.name ?: continue
            val fmt = (file.format ?: "").lowercase()
            val isVideo = listOf("h.264", "mpeg4", "ogg video").any { fmt.contains(it) } &&
                !name.endsWith(".jpg") && !name.endsWith(".png") && !name.endsWith(".pdf")
            if (isVideo) {
                val quality = if (fmt.contains("h.264")) Qualities.P720.value else Qualities.P480.value
                callback(
                    newExtractorLink(
                        this.name,
                        this.name,
                        "$server$dir/$name",
                    ) {
                        this.quality = quality
                        this.type = ExtractorLinkType.VIDEO
                    }
                )
                found = true
            }
        }
        return found
    }
}
