(() => {
  const latestReleaseApi =
    "https://api.github.com/repos/TadatsuneSakamoto/RubiMorph/releases/latest";

  const latestReleasePage =
    "https://github.com/TadatsuneSakamoto/RubiMorph/releases/latest";

  const elements = {
    status: document.getElementById("release-status"),
    date: document.getElementById("release-date"),
    tag: document.getElementById("release-tag"),
    releaseLink: document.getElementById("release-link"),
    installerLink: document.getElementById("installer-link"),
    installerName: document.getElementById("installer-name"),
    installerDetail: document.getElementById("installer-detail"),
    portableLink: document.getElementById("portable-link"),
    portableName: document.getElementById("portable-name"),
    portableDetail: document.getElementById("portable-detail"),
    checksumLink: document.getElementById("checksum-link")
  };

  const setHref = (element, href) => {
    if (element && href) {
      element.href = href;
    }
  };

  const formatBytes = (bytes) => {
    if (!Number.isFinite(bytes) || bytes <= 0) {
      return "";
    }

    const units = ["B", "KB", "MB", "GB"];
    let value = bytes;
    let unitIndex = 0;

    while (value >= 1024 && unitIndex < units.length - 1) {
      value /= 1024;
      unitIndex += 1;
    }

    const fractionDigits =
      unitIndex === 0 || value >= 10 ? 0 : 1;

    return `${value.toFixed(fractionDigits)} ${units[unitIndex]}`;
  };

  const formatDate = (value) => {
    if (!value) {
      return "";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
      return "";
    }

    return new Intl.DateTimeFormat("ja-JP", {
      year: "numeric",
      month: "long",
      day: "numeric"
    }).format(date);
  };

  const setFallbackLinks = () => {
    setHref(elements.releaseLink, latestReleasePage);
    setHref(elements.installerLink, latestReleasePage);
    setHref(elements.portableLink, latestReleasePage);
    setHref(elements.checksumLink, latestReleasePage);
  };

  fetch(latestReleaseApi, {
    headers: {
      Accept: "application/vnd.github+json"
    }
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error(`GitHub API returned ${response.status}`);
      }

      return response.json();
    })
    .then((release) => {
      const assets =
        Array.isArray(release.assets) ? release.assets : [];

      const installer = assets.find((asset) =>
        /^RubiMorphSetup-.*\.exe$/i.test(asset.name)
      );

      const portable = assets.find((asset) =>
        /^RubiMorphPortable-.*\.zip$/i.test(asset.name)
      );

      const checksum = assets.find((asset) =>
        /^SHA256SUMS\.txt$/i.test(asset.name)
      );

      const releaseName =
        release.name || release.tag_name || "ææ°ç";

      const releaseUrl =
        release.html_url || latestReleasePage;

      const publishedDate =
        formatDate(release.published_at);

      if (elements.status) {
        elements.status.textContent =
          `${releaseName} ãå¬éãã¦ãã¾ãã`;
      }

      if (elements.date) {
        elements.date.textContent =
          publishedDate ? `å¬éæ¥: ${publishedDate}` : "";
      }

      if (elements.tag) {
        elements.tag.textContent =
          release.tag_name ? `ã¿ã°: ${release.tag_name}` : "";
      }

      setHref(elements.releaseLink, releaseUrl);

      if (installer) {
        setHref(
          elements.installerLink,
          installer.browser_download_url
        );

        if (elements.installerName) {
          elements.installerName.textContent = installer.name;
        }

        if (elements.installerDetail) {
          const size = formatBytes(installer.size);
          elements.installerDetail.textContent =
            size
              ? `Windowsã¤ã³ã¹ãã¼ã©ã¼ / ${size}`
              : "Windowsã¤ã³ã¹ãã¼ã©ã¼";
        }
      } else {
        setHref(elements.installerLink, releaseUrl);
      }

      if (portable) {
        setHref(
          elements.portableLink,
          portable.browser_download_url
        );

        if (elements.portableName) {
          elements.portableName.textContent = portable.name;
        }

        if (elements.portableDetail) {
          const size = formatBytes(portable.size);
          elements.portableDetail.textContent =
            size
              ? `ãã¼ã¿ãã«ç / ${size}`
              : "ãã¼ã¿ãã«ç";
        }
      } else {
        setHref(elements.portableLink, releaseUrl);
      }

      setHref(
        elements.checksumLink,
        checksum?.browser_download_url || releaseUrl
      );
    })
    .catch(() => {
      if (elements.status) {
        elements.status.textContent =
          "ææ°çãGitHub Releasesã§å¬éãã¦ãã¾ãã";
      }

      if (elements.date) {
        elements.date.textContent = "";
      }

      if (elements.tag) {
        elements.tag.textContent = "";
      }

      setFallbackLinks();
    });
})();

