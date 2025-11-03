/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, useRef, onMounted, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { _t } from "@web/core/l10n/translation";

export class ImageAnnotationWidget extends Component {
    setup() {
        this.orm = useService("orm");
        this.dialog = useService("dialog");
        this.notification = useService("notification");
        
        this.state = useState({
            imageLoaded: false,
            annotations: [],
            showPopup: false,
            currentAnnotation: null,
            popupPosition: { x: 0, y: 0 }
        });

        this.imageRef = useRef("annotationImage");
        this.containerRef = useRef("imageContainer");

        onMounted(() => {
            console.log('[ImageAnnotation] Component mounted');
            console.log('[ImageAnnotation] Props:', this.props);
            this.loadAnnotations();
        });

        onWillUpdateProps((nextProps) => {
            console.log('[ImageAnnotation] Props will update');
            this.loadAnnotations();
        });
    }

    async loadAnnotations() {
        if (!this.props.record.resId) {
            console.log('[ImageAnnotation] No record ID, skipping annotation load');
            return;
        }
        
        console.log('[ImageAnnotation] Loading annotations for record:', this.props.record.resId);
        
        try {
            const annotations = await this.orm.searchRead(
                "project.image.annotation.point",
                [["annotation_id", "=", this.props.record.resId]],
                ["numero", "descripcion", "secuencia", "pos_x", "pos_y", "color", "estado"]
            );
            
            console.log('[ImageAnnotation] Loaded annotations:', annotations.length);
            this.state.annotations = annotations;
        } catch (error) {
            console.error('[ImageAnnotation] Error loading annotations:', error);
        }
    }
    
    get hasImage() {
        const record = this.props.record;
        // Verificar si hay un resId (registro guardado) y si el campo image tiene valor
        const hasResId = !!record.resId;
        const hasImageData = record.data && record.data.image;
        
        console.log('[ImageAnnotation] Has resId:', hasResId);
        console.log('[ImageAnnotation] Has image data:', !!hasImageData);
        
        return hasResId && hasImageData;
    }

    get imageUrl() {
        const record = this.props.record;
        
        console.log('[ImageAnnotation] ===== DEBUG IMAGE URL =====');
        console.log('[ImageAnnotation] Record:', record);
        console.log('[ImageAnnotation] Record.data:', record.data);
        console.log('[ImageAnnotation] Record.resId:', record.resId);
        console.log('[ImageAnnotation] Props.value:', this.props.value);
        
        // Si no hay resId, no podemos cargar la imagen
        if (!record.resId) {
            console.log('[ImageAnnotation] No resId, cannot load image');
            return null;
        }
        
        // En Odoo, los campos Binary generalmente se acceden por URL, no por base64 directo
        // Construir URL para acceder a la imagen
        const imageUrl = `/web/image?model=project.image.annotation&id=${record.resId}&field=image&unique=${Date.now()}`;
        console.log('[ImageAnnotation] Using image URL:', imageUrl);
        
        return imageUrl;
    }

    onImageLoad(ev) {
        console.log('[ImageAnnotation] Image loaded successfully:', ev.target.naturalWidth, 'x', ev.target.naturalHeight);
        this.state.imageLoaded = true;
    }
    
    onImageError(ev) {
        console.error('[ImageAnnotation] Error loading image:', ev);
        console.error('[ImageAnnotation] Image src:', ev.target?.src?.substring(0, 100));
        
        this.notification.add(
            "Error al cargar la imagen. Esto puede deberse a:\n" +
            "1. Formato de imagen no compatible\n" +
            "2. Imagen corrupta o dañada\n" +
            "3. Intenta subir la imagen de nuevo\n\n" +
            "Formatos soportados: JPG, PNG, GIF, WebP", 
            { 
                type: "danger",
                sticky: true 
            }
        );
        
        this.state.imageLoaded = false;
    }

    async onImageClick(ev) {
        if (!this.state.imageLoaded) return;
        
        // Verificar que el registro esté guardado
        if (!this.props.record.resId) {
            this.notification.add("Por favor, guarda el registro antes de agregar anotaciones", { 
                type: "warning" 
            });
            return;
        }

        const rect = ev.currentTarget.getBoundingClientRect();
        const x = ((ev.clientX - rect.left) / rect.width) * 100;
        const y = ((ev.clientY - rect.top) / rect.height) * 100;

        // Verificar si se hizo clic en una anotación existente
        const clickedAnnotation = this.findAnnotationAtPosition(x, y);
        
        if (clickedAnnotation) {
            this.showAnnotationDetails(clickedAnnotation, ev.clientX, ev.clientY);
        } else {
            await this.createNewAnnotation(x, y, ev.clientX, ev.clientY);
        }
    }

    findAnnotationAtPosition(x, y) {
        const threshold = 3; // 3% de tolerancia para el clic
        return this.state.annotations.find(ann => 
            Math.abs(ann.pos_x - x) < threshold && 
            Math.abs(ann.pos_y - y) < threshold
        );
    }

    showAnnotationDetails(annotation, clientX, clientY) {
        this.state.currentAnnotation = annotation;
        this.state.popupPosition = { x: clientX, y: clientY };
        this.state.showPopup = true;
    }

    async createNewAnnotation(x, y, clientX, clientY) {
        const nextNumero = this.state.annotations.length > 0 
            ? Math.max(...this.state.annotations.map(a => a.numero)) + 1 
            : 1;

        this.state.currentAnnotation = {
            annotation_id: this.props.record.resId,
            numero: nextNumero,
            descripcion: '',
            secuencia: nextNumero * 10,
            pos_x: x,
            pos_y: y,
            color: '#FF0000',
            estado: 'pendiente',
            isNew: true
        };
        
        this.state.popupPosition = { x: clientX, y: clientY };
        this.state.showPopup = true;
    }

    closePopup() {
        this.state.showPopup = false;
        this.state.currentAnnotation = null;
    }

    async saveAnnotation() {
        const data = this.state.currentAnnotation;
        
        if (!data.descripcion) {
            this.notification.add("La descripción es requerida", { type: "warning" });
            return;
        }

        try {
            if (data.isNew) {
                delete data.isNew;
                await this.orm.create("project.image.annotation.point", [data]);
                this.notification.add("Anotación creada exitosamente", { type: "success" });
            } else {
                const { id, ...updateData } = data;
                await this.orm.write("project.image.annotation.point", [id], updateData);
                this.notification.add("Anotación actualizada exitosamente", { type: "success" });
            }
            
            await this.loadAnnotations();
            this.closePopup();
        } catch (error) {
            this.notification.add("Error al guardar la anotación: " + error.message, { type: "danger" });
        }
    }

    async deleteAnnotation() {
        if (!this.state.currentAnnotation.id) {
            this.closePopup();
            return;
        }

        try {
            await this.orm.unlink("project.image.annotation.point", [this.state.currentAnnotation.id]);
            this.notification.add("Anotación eliminada exitosamente", { type: "success" });
            await this.loadAnnotations();
            this.closePopup();
        } catch (error) {
            this.notification.add("Error al eliminar la anotación: " + error.message, { type: "danger" });
        }
    }

    updateField(field, value) {
        this.state.currentAnnotation[field] = value;
    }

    getArrowStyle(annotation) {
        return `left: ${annotation.pos_x}%; top: ${annotation.pos_y}%; border-color: ${annotation.color};`;
    }

    getNumberStyle(annotation) {
        return `left: ${annotation.pos_x}%; top: ${annotation.pos_y}%; background-color: ${annotation.color};`;
    }
}

ImageAnnotationWidget.template = "project_image_annotation.ImageAnnotationWidget";
ImageAnnotationWidget.props = {
    record: Object,
};

registry.category("fields").add("image_annotation_widget", {
    component: ImageAnnotationWidget,
});
