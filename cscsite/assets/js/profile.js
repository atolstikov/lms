!function(a,b,c){"use strict";var d={upload:a("#templateUpload").html(),thumb:a("#templateThumb").html()},e={unknownError:"Неизвестная ошибка.",badRequest:"Неверный запрос.",uploadError:"Ошибка загрузки файла на сервер. Код: ",thumbDoneFail:"Ошибка создания превью. Код: ",thumbSuccess:"Превью успешно создано",imgDimensions:"Не удалось получить размеры изображения",preloadError:"Ошибка инициализации"},f=void 0!==c.photo?c.photo:{},g={minWidth:250,minHeight:350,maxFileSize:5,minThumbWidth:170,minThumbHeight:238},h={url:"/profile-update-image/",data:{user_id:c.user_id},headers:{"X-CSRFToken":a.cookie("csrftoken")}},i=a("#user-photo-upload"),j=(a(".modal-header",i),a(".modal-body",i)),k={init:function(){if(void 0!==c.user_id){var b=a.Deferred(),d=b;a.each(c.preload,function(b,c){d=d.then(function(){return a.ajax({url:c,dataType:"script",cache:!0})})}),d.done(function(){a("a[href=#user-photo-upload]").click(function(){i.modal("toggle"),void 0===f&&k.uploadInit()}),i.one("shown.bs.modal",function(){void 0!==f&&k.thumbInit(f)})}).fail(function(){k.showError(e.preloadError)}),b.resolve()}},showError:function(b){a.jGrowl(b,{theme:"error",position:"bottom-right"})},showMessage:function(b){a.jGrowl(b,{position:"bottom-right"})},uploadInit:function(){var a=document.getElementById("simple-btn");FileAPI.event.off(a,"change",k.uploadValidate),j.html(d.upload),a=document.getElementById("simple-btn"),FileAPI.event.on(a,"change",k.uploadValidate)},uploadValidate:function(a){var b=FileAPI.getFiles(a);FileAPI.filterFiles(b,function(a,b){return/^image/.test(a.type)&&b?b.width>=g.minWidth&&b.height>=g.minHeight&&a.size<=g.maxFileSize*FileAPI.MB:void 0},function(a,c){a.length&&k.uploadProgress(b[0])})},enableLoadingState:function(){j.addClass("load-state")},disableLoadingState:function(){j.removeClass("load-state")},uploadProgress:function(a){var b=FileAPI.extend({},h,{files:{photo:a},upload:function(){k.enableLoadingState()},complete:function(b,c){if(b)k.uploadError(c);else{var d=JSON.parse(c.response);k.uploadSuccess(d,a)}}});FileAPI.upload(b)},uploadError:function(a){k.disableLoadingState();var b;switch(a.status){case 500:b=e.unknownError;break;case 403:b=e.badRequest;break;default:b=a.response}k.showError(e.uploadError+b)},uploadSuccess:function(a,b){1==a.success?FileAPI.getInfo(b,function(b,c){b?k.showError(e.imgDimensions):(a.width=c.width,a.height=c.height,f=a,k.thumbInit(a))}):k.showError(e.unknownError)},thumbInit:function(a){k.enableLoadingState(),a.url=a.url+"?"+Math.floor(Date.now()/1e3);var c=j.width()-40,e=Math.round(c/a.width*a.height);j.html(b.template(d.thumb,{url:a.url,width:c,height:e}));var f=j.find(".uploaded-img")[0],h=new Cropper(f,{viewMode:1,background:!0,responsive:!1,scalable:!1,autoCropArea:1,aspectRatio:5/7,dragMode:"move",guides:!1,movable:!1,rotatable:!1,zoomable:!1,zoomOnTouch:!1,zoomOnWheel:!1,minContainerWidth:250,minContainerHeight:250,offsetWidth:0,offsetHeight:0,minCropBoxWidth:g.minThumbWidth,minCropBoxHeight:g.minThumbHeight,built:function(){j.find(".-prev").click(function(){k.uploadInit()}),j.find(".save-crop-data").click(function(){k.thumbDone(h)}),k.setCropBox(h),k.disableLoadingState()}})},thumbDone:function(b){b.disable();var c=k.getCropBox(b),d=a.extend({crop_data:!0},c),f=a.extend(!0,{},h,{method:"POST",dataType:"json",data:d});a.ajax(f).done(function(a){b.enable(),1==a.success?k.thumbSuccess(b,a):k.showError(a.reason)}).fail(function(a){b.enable(),k.showError(e.thumbDoneFail+a.statusText)})},getCropBox:function(a){var b=a.getData(!0);return b},setCropBox:function(a){if(void 0!==f.cropbox){var b=f.cropbox;a.setData(b)}},thumbSuccess:function(b,c){b.enable(),a(".thumbnail-img img").attr("src",c.thumbnail),k.showMessage(e.thumbSuccess),i.modal("hide")}};a(function(){k.init()})}($,_,profileAppInit);