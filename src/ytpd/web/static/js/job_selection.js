(() => {
  let selectedJobId = "";

  function shortId(jobId) {
    return jobId.slice(0, 8);
  }

  function pickPreferredJob(jobs) {
    if (!Array.isArray(jobs) || jobs.length === 0) {
      return null;
    }
    return (
      jobs.find((job) => job.status === "running" || job.status === "interrupted") ||
      jobs[0]
    );
  }

  function setSelectedJobId(jobId) {
    if (selectedJobId === jobId) {
      window.dispatchEvent(
        new CustomEvent("ytpd-job-selected", { detail: { jobId: selectedJobId } })
      );
      return;
    }
    selectedJobId = jobId;
    window.dispatchEvent(
      new CustomEvent("ytpd-job-selected", { detail: { jobId: selectedJobId } })
    );
  }

  function clearSelectedJobId() {
    selectedJobId = "";
    window.dispatchEvent(
      new CustomEvent("ytpd-job-cleared", { detail: { jobId: "" } })
    );
  }

  window.YtpdJobSelection = {
    getSelectedJobId() {
      return selectedJobId;
    },
    setSelectedJobId,
    clearSelectedJobId,
    shortId,
    pickPreferredJob,
  };
})();
