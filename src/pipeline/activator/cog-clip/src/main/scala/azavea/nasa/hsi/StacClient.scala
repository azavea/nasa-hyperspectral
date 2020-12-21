package azavea.nasa.hsi

import com.azavea.stac4s._
import io.lemonlabs.uri.Url

case class StacClient(stac_api_url: Url) {
  def getStacItem(itemId: String): StacItem = ???

  def getStacCollection(collection: String): Option[StacCollection] = ???

  def postStacCollection(collection: StacCollection): Unit = ???

  def postStacCollectionItem(collection: String, item: StacItem): Unit = ???
}
