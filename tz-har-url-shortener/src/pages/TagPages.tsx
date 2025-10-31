import { useState, useEffect, type FormEvent } from "react";
import Modal from "../components/Modal";
import { useAuth } from "../context/AuthContext";
import type { UrlTag } from "../types/URL";
import { TzHarAPIError } from "../services/TzHarAPIError";
import { api } from "../services/TzHarApi";
import LoadingSpinner from "../components/LoadingSpinner";


const TagsPage: React.FC = () => {
  const [tags, setTags] = useState<UrlTag[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingTag, setEditingTag] = useState<UrlTag | null>(null);
  
  const [name, setName] = useState('');
  const [color, setColor] = useState('#cccccc');
  const [descr, setDescr] = useState('');

  const { showNotification } = useAuth();
  
  const fetchTags = async () => {
    setIsLoading(true);
    try {
      const data = await api.tag.getUserTags();
      setTags(data.results);
    } catch (error) {
       const msg = error instanceof TzHarAPIError ? error.message : 'Erro ao carregar tags';
       showNotification(msg, 'error');
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchTags();
  }, []);
  
  const openCreateModal = () => {
    setEditingTag(null);
    setName('');
    setColor('#cccccc');
    setDescr('');
    setIsModalOpen(true);
  };
  
  const openEditModal = (tag: UrlTag) => {
    setEditingTag(tag);
    setName(tag.name);
    setColor(tag.color);
    setDescr(tag.descr || '');
    setIsModalOpen(true);
  };

  const closeModal = () => {
    setIsModalOpen(false);
    setEditingTag(null);
  };

  const handleSubmit = async (e: FormEvent) => {
    e.preventDefault();
    try {
      if (editingTag) {
        // Atualizar
        const updatedTag = await api.tag.updateTag({ id: editingTag.id, name, color, descr });
        setTags(tags.map(t => t.id === updatedTag.id ? updatedTag : t));
        showNotification('Tag atualizada!', 'success');
      } else {
        // Criar
        const newTag = await api.tag.createTag({ name, color, descr });
        setTags([newTag, ...tags]);
        showNotification('Tag criada!', 'success');
      }
      closeModal();
    } catch (error) {
      const msg = error instanceof TzHarAPIError ? error.message : 'Erro ao salvar tag';
      showNotification(msg, 'error');
    }
  };
  
  const handleDelete = async (id: number) => {
    if (window.confirm('Tem certeza que deseja deletar esta tag? Isso não deleta as URLs, apenas a tag.')) {
       try {
        await api.tag.deleteTag(id);
        setTags(tags.filter(t => t.id !== id));
        showNotification('Tag deletada.', 'success');
      } catch (error) {
        const msg = error instanceof TzHarAPIError ? error.message : 'Erro ao deletar tag';
        showNotification(msg, 'error');
      }
    }
  };

  return (
    <div className="page-content">
      <div className="page-header">
        <h1>Gerenciar Tags</h1>
        <button className="btn btn-primary" onClick={openCreateModal}>+ Nova Tag</button>
      </div>

      {isLoading ? <LoadingSpinner /> : (
        <div className="tag-list">
          {tags.length === 0 ? <p>Você ainda não criou nenhuma tag.</p> : (
            tags.map(tag => (
              <div key={tag.id} className="tag-card">
                <span className="tag-pill" style={{ backgroundColor: tag.color }}>{tag.name}</span>
                <p>{tag.descr || 'Sem descrição'}</p>
                <div className="button-group">
                  <button className="btn btn-secondary" onClick={() => openEditModal(tag)}>Editar</button>
                  <button className="btn btn-danger" onClick={() => handleDelete(tag.id)}>Deletar</button>
                  {/* TODO: Botão para limpar tags (clearTag) ou ver URLs (getUrlsFromTag) */}
                </div>
              </div>
            ))
          )}
        </div>
      )}
      
      <Modal 
        isOpen={isModalOpen} 
        onClose={closeModal} 
        title={editingTag ? 'Editar Tag' : 'Nova Tag'}
      >
        <form onSubmit={handleSubmit} className="modal-form">
          <div className="form-group">
            <label htmlFor="tag-name">Nome</label>
            <input 
              id="tag-name" 
              type="text" 
              value={name} 
              onChange={e => setName(e.target.value)} 
              required 
            />
          </div>
           <div className="form-group">
            <label htmlFor="tag-color">Cor</label>
            <input 
              id="tag-color" 
              type="color" 
              value={color} 
              onChange={e => setColor(e.target.value)} 
              required 
            />
          </div>
           <div className="form-group">
            <label htmlFor="tag-descr">Descrição (Opcional)</label>
            <textarea
              id="tag-descr"
              value={descr}
              onChange={e => setDescr(e.target.value)}
            />
          </div>
          <button type="submit" className="btn btn-primary">
            {editingTag ? 'Atualizar' : 'Criar'}
          </button>
        </form>
      </Modal>
    </div>
  );
};


export default TagsPage;