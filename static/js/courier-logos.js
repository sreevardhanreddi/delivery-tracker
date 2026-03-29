// Courier service logos configuration
const courierLogos = {
  bluedart: {
    name: "BlueDart",
    color: "bg-blue-500",
    logo: "/static/images/logos/bluedart.png",
    alt: "BlueDart Logo",
    trackUrl: "https://www.bluedart.com/?{trackingNumber}",
  },
  dtdc: {
    name: "DTDC",
    color: "bg-green-500",
    logo: "/static/images/logos/dtdc.png",
    alt: "DTDC Logo",
    trackUrl: "https://www.dtdc.com/track-your-shipment/?awb={trackingNumber}",
  },
  delhivery: {
    name: "Delhivery",
    color: "bg-purple-500",
    logo: "/static/images/logos/delhivery.png",
    alt: "Delhivery Logo",
    trackUrl: "https://www.delhivery.com/track-v2/package/{trackingNumber}",
  },
  shadow_fax: {
    name: "ShadowFax",
    color: "bg-yellow-500",
    logo: "/static/images/logos/shadowfax.png",
    alt: "ShadowFax Logo",
    trackUrl: "https://tracker.shadowfax.in/#/track/{trackingNumber}",
  },
  ecom_express: {
    name: "Ecom Express",
    color: "bg-red-500",
    logo: "/static/images/logos/ecomexpress.png",
    alt: "Ecom Express Logo",
    trackUrl: "https://www.delhivery.com/track-v2/package/{trackingNumber}",
  },
  ekart: {
    name: "Ekart",
    color: "bg-red-500",
    logo: "/static/images/logos/ekart.png",
    alt: "Ekart Logo",
    trackUrl:
      "https://ekartlogistics.com/ekartlogistics-web/shipmenttrack/{trackingNumber}",
  },
  unknown: {
    name: "Unknown",
    color: "bg-gray-500",
    logo: "/static/images/logos/unknown.jpg",
    alt: "Unknown Courier Logo",
    trackUrl: "https://www.bluedart.com/?{trackingNumber}",
  },
};

// Function to get courier service details from tracking number
function getCourierService(service) {
  if (!service) return courierLogos.unknown;

  const number = service.toLowerCase();

  if (service === "bluedart") {
    return courierLogos.bluedart;
  } else if (service === "dtdc") {
    return courierLogos.dtdc;
  } else if (service === "delhivery") {
    return courierLogos.delhivery;
  } else if (service === "shadow_fax") {
    return courierLogos.shadow_fax;
  } else if (service === "ecom_express") {
    return courierLogos.ecom_express;
  } else if (service === "ekart") {
    return courierLogos.ekart;
  } else {
    return courierLogos.unknown;
  }
}
