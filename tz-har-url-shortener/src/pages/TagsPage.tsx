import { useState } from "react";
import { Plus, Trash2, Tag, X } from "lucide-react";
import { useUrlTags } from "../context/TagContext";
import { api } from "../services/TzHarApi";
import { Constants } from "../util/Constants";
import { useDialog } from "../hooks/useDialog";
import { useUrls } from "../context/UrlsContext";

export default function TagsPage() {

  const { showConfirm, showAlert, AlertRenderer, ConfirmRenderer } = useDialog()

  const { urls, setUrls } = useUrls()
  const { tags, setTags } = useUrlTags();

  const [showTagModal, setShowTagModal] = useState(false);
  const [newTagName, setNewTagName] = useState("");
  const [newTagDescription, setNewTagDescription] = useState("");
  const [newTagColor, setNewTagColor] = useState("#3B82F6");

  const handleDeleteTag = async (id: number) => {
    const confirm = await showConfirm("Delete this tag?")
    if (!confirm) return;

    try {
      await api.tag.deleteTag(id);
      setTags(tags.filter(tag => tag.id !== id))
      setUrls(urls.map(url => {return {
        ...url, tags: url.tags.filter(tag => tag.id !== id)
      }}))
    } catch (error: any) {
      showAlert("Error deleting tag: " + error.message)
    }
  };

  const clearModal = () => {
    setNewTagName("");
    setNewTagDescription("");
    setNewTagColor("#3B82F6");
    setShowTagModal(false);
  }

  const handleCreateTag = async () => {
    if (!newTagName) return;

    try {
      const urlTag = await api.tag.createTag({
        name: newTagName,
        color: newTagColor,
        descr: newTagDescription || undefined,
      });
      clearModal()
      setTags([...[urlTag], ...tags])
    } catch (error: any) {
      showAlert("Error creating tag: " + error.message)
    }
  };

  return (
    <>
      <div className="space-y-6">
        <div className="flex items-center justify-between">
          <h2 className="text-2xl font-bold text-slate-900">Tags</h2>
          <button
            onClick={() => setShowTagModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 hover:shadow-lg transition-all duration-200 shadow-md active:scale-95"
          >
            <Plus className="w-5 h-5" />
            New Tag
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {tags.map((tag) => (
  <div
    key={tag.id}
    className="bg-white rounded-xl shadow-sm border border-slate-200 p-6 hover:shadow-md hover:border-slate-300 transition"
  >
    <div className="flex items-start justify-between mb-3">
      <div className="flex items-center gap-3 min-w-0">
        <div
          className="w-10 h-10 rounded-lg flex-shrink-0"
          style={{ backgroundColor: tag.color }}
        />
        <div className="min-w-0 max-w-full overflow-hidden">
          <h3 className="font-medium text-slate-900 truncate break-all">
            {tag.name}
          </h3>
          <p className="text-xs text-slate-500 truncate">{tag.color}</p>
        </div>
      </div>
      <button
        onClick={() => handleDeleteTag(tag.id)}
        className="p-2 text-rose-600 hover:bg-rose-50 rounded-lg transition-all duration-200 hover:shadow-sm active:scale-90 flex-shrink-0"
      >
        <Trash2 className="w-5 h-5" />
      </button>
    </div>

    {tag.descr && (
      <p className="text-sm text-slate-600 line-clamp-2 mt-2 break-words">
        {tag.descr}
      </p>
    )}
  </div>
))}
        </div>
      </div>

      {/* Tag Modal */}
      {showTagModal && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-2xl shadow-2xl border border-slate-200 w-full max-w-lg p-6 max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-violet-100 rounded-xl flex items-center justify-center">
                  <Tag className="w-6 h-6 text-violet-600" />
                </div>
                <h3 className="text-xl font-bold text-slate-900">
                  Create New Tag
                </h3>
              </div>
              <button
                onClick={() => {
                  setShowTagModal(false);
                  setNewTagName("");
                  setNewTagDescription("");
                  setNewTagColor("#3B82F6");
                }}
                className="p-2 text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-all duration-200 active:scale-90"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="space-y-5">
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Tag Name <span className="text-rose-500">*</span>
                </label>
                <input
                  type="text"
                  value={newTagName}
                  onChange={(e) => setNewTagName(e.target.value)}
                  onKeyDown={(e) =>
                    e.key === "Enter" && !e.shiftKey && handleCreateTag()
                  }
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none"
                  placeholder="e.g., Work, Personal, Important"
                  maxLength={64}
                />
                <p className="text-xs text-slate-500 mt-1">
                  {newTagName.length}/64 characters
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-2">
                  Description{" "}
                  <span className="text-slate-400 text-xs">(optional)</span>
                </label>
                <textarea
                  value={newTagDescription}
                  onChange={(e) => setNewTagDescription(e.target.value)}
                  className="w-full px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none resize-none"
                  placeholder="Add a description for this tag..."
                  rows={3}
                  maxLength={256}
                />
                <p className="text-xs text-slate-500 mt-1">
                  {newTagDescription.length}/256 characters
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-slate-700 mb-3">
                  Tag Color
                </label>

                {/* Color Preview */}
                <div className="mb-4">
                  <div className="flex items-center gap-3 p-4 bg-slate-50 rounded-lg border border-slate-200">
                    <div
                      className="w-12 h-12 rounded-lg shadow-sm border-2 border-white"
                      style={{ backgroundColor: newTagColor }}
                    />
                    <div className="flex-1">
                      <p className="text-sm text-slate-600 mb-1">
                        Selected Color
                      </p>
                      <p className="text-sm font-mono font-medium text-slate-900">
                        {newTagColor.toUpperCase()}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Color Presets */}
                <div className="mb-4">
                  <p className="text-xs font-medium text-slate-600 mb-2">
                    Quick Select
                  </p>
                  <div className="grid grid-cols-9 gap-2">
                    {Constants.COLOR_PRESSETS.map((color) => (
                      <button
                        key={color}
                        onClick={() => setNewTagColor(color)}
                        className={`w-8 h-8 rounded-lg transition-all duration-200 hover:scale-110 ${
                          newTagColor === color
                            ? "ring-2 ring-offset-2 ring-indigo-500 scale-110"
                            : "hover:shadow-md"
                        }`}
                        style={{ backgroundColor: color }}
                        title={color}
                      />
                    ))}
                  </div>
                </div>

                {/* Custom Color Picker */}
                <div>
                  <p className="text-xs font-medium text-slate-600 mb-2">
                    Custom Color
                  </p>
                  <div className="flex gap-3">
                    <input
                      type="color"
                      value={newTagColor}
                      onChange={(e) => setNewTagColor(e.target.value)}
                      className="h-12 w-20 rounded-lg border-2 border-slate-300 cursor-pointer hover:border-indigo-400 transition-colors"
                    />
                    <input
                      type="text"
                      value={newTagColor}
                      onChange={(e) => {
                        const value = e.target.value;
                        if (/^#[0-9A-Fa-f]{0,6}$/.test(value)) {
                          setNewTagColor(value);
                        }
                      }}
                      className="flex-1 px-4 py-3 border border-slate-300 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 outline-none font-mono text-sm"
                      placeholder="#3B82F6"
                      maxLength={7}
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={() => {
                    setShowTagModal(false);
                    setNewTagName("");
                    setNewTagDescription("");
                    setNewTagColor("#3B82F6");
                  }}
                  className="flex-1 px-4 py-3 bg-slate-100 text-slate-700 rounded-lg font-medium hover:bg-slate-200 transition-all duration-200 active:scale-98"
                >
                  Cancel
                </button>
                <button
                  onClick={handleCreateTag}
                  disabled={!newTagName}
                  className="flex-1 px-4 py-3 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 hover:shadow-lg transition-all duration-200 shadow-md active:scale-98 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  Create Tag
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
      {AlertRenderer}
      {ConfirmRenderer}
    </>
  );
}
