/// <reference path="../pb_data/types.d.ts" />
migrate((app) => {
  const collection = app.findCollectionByNameOrId("pbc_3710182791")

  // add field
  collection.fields.addAt(1, new Field({
    "help": "",
    "hidden": false,
    "id": "file4262580536",
    "maxSelect": 0,
    "maxSize": 0,
    "mimeTypes": null,
    "name": "Name",
    "presentable": false,
    "protected": false,
    "required": false,
    "system": false,
    "thumbs": null,
    "type": "file"
  }))

  // add field
  collection.fields.addAt(2, new Field({
    "help": "",
    "hidden": false,
    "id": "file753727511",
    "maxSelect": 0,
    "maxSize": 0,
    "mimeTypes": null,
    "name": "Type",
    "presentable": false,
    "protected": false,
    "required": false,
    "system": false,
    "thumbs": null,
    "type": "file"
  }))

  return app.save(collection)
}, (app) => {
  const collection = app.findCollectionByNameOrId("pbc_3710182791")

  // remove field
  collection.fields.removeById("file4262580536")

  // remove field
  collection.fields.removeById("file753727511")

  return app.save(collection)
})
