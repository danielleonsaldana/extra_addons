/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, useState, useRef, onMounted, onWillUpdateProps } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

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
            this.loadAnnotations();
        });

        onWillUpdateProps(() => {
            this.loadAnnotations();
        });
    }

    async loadAnnotations() {
        if (!this.props.record.data.id) return;
        
        const annotations = await this.orm.searchRead(
            "project.image.annotation.point",
            [["annotation_id", "=", this.props.record.data.id]],
            ["numero", "descripcion", "secuencia", "pos_x", "pos_y", "color", "estado"]
        );
        
        this.state.annotations = annotations;
    }

    get imageUrl() {
        if (!this.props.record.data.image) return null;
        return `data:image/png;base64,${this.props.record.data.image}`;
    }

    onImageLoad() {
        this.state.imageLoaded = true;
    }

    async onImageClick(ev) {
        if (!this.state.imageLoaded) return;
        
        // Verificar que el registro esté guardado
        if (!this.props.record.data.id) {
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
            annotation_id: this.props.record.data.id,
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
