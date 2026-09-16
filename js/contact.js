// Prepare a WhatsApp conversation without submitting or storing data on this site.
(() => {
    'use strict';

    function initializeContactForm() {
        const form = document.getElementById('contactForm');
        if (!form || form.dataset.contactReady) return;
        const names = ['name', 'phone', 'subject', 'message'];
        const fields = Object.fromEntries(names.map(name => [name, form.elements.namedItem(name)]));
        if (names.some(name => !fields[name])) return;

        let feedback = form.querySelector('.form-message');
        if (!feedback) {
            feedback = document.createElement('p');
            feedback.className = 'form-message';
            form.append(feedback);
        }
        feedback.id ||= 'contactFormMessage';
        feedback.setAttribute('role', 'status');
        feedback.setAttribute('aria-live', 'polite');
        feedback.setAttribute('aria-atomic', 'true');
        feedback.hidden = !feedback.textContent.trim();

        const context = form.querySelector('#contact-context');
        if (context) {
            context.setAttribute('role', 'status');
            context.setAttribute('aria-live', 'polite');
            context.setAttribute('aria-atomic', 'true');
        }

        let opening = false;
        let invalidField = null;
        const submit = form.querySelector('[type="submit"]');
        const submitContent = submit ? [...submit.childNodes].map(node => node.cloneNode(true)) : [];
        const studio = form.closest('.contact-studio');
        const experience = form.closest('.contact-experience');
        const preview = studio ? studio.querySelector('[data-contact-preview]') : null;
        const previewFields = preview ? {
            greeting: preview.querySelector('[data-preview-greeting]'),
            subject: preview.querySelector('[data-preview-subject]'),
            message: preview.querySelector('[data-preview-message]')
        } : null;
        const hasPreview = previewFields && Object.values(previewFields).every(Boolean);
        const progress = form.querySelector('.contact-progress');
        const counter = form.querySelector('#message-count');

        function plausiblePhone(value) {
            const digits = value.replace(/\D/g, '');
            return /^[+\d\s().-]+$/.test(value) && digits.length >= 10 && digits.length <= 15;
        }

        function updateExperience() {
            const data = Object.fromEntries(names.map(name => [name, String(fields[name].value || '').trim()]));
            if (hasPreview) {
                previewFields.greeting.textContent = data.name ? 'Olá, sou ' + data.name + '.' : 'Olá, gostaria de conversar com o escritório.';
                previewFields.subject.textContent = data.subject ? 'Gostaria de orientação em ' + data.subject + '.' : 'Vou contar um pouco sobre a minha situação.';
                const characters = Array.from(data.message);
                previewFields.message.textContent = characters.length > 180 ? characters.slice(0, 179).join('') + '…' : data.message || 'Seu resumo aparecerá aqui enquanto você escreve.';
            }
            if (counter) {
                const count = fields.message.value.length.toLocaleString('pt-BR');
                const limit = fields.message.maxLength;
                counter.textContent = count + (limit > 0 ? ' / ' + limit.toLocaleString('pt-BR') : ' caracteres');
            }
            if (progress) {
                const completed = [Boolean(data.name && plausiblePhone(data.phone)), Boolean(data.subject), Boolean(data.message)];
                const current = completed.indexOf(false);
                ['contact', 'subject', 'message'].forEach((name, index) => {
                    const step = progress.querySelector('[data-progress-step="' + name + '"]');
                    if (!step) return;
                    step.classList.toggle('is-complete', completed[index]);
                    step.classList.toggle('is-current', index === current);
                });
            }
        }

        function revealExperience() {
            // These are visual summaries of the fields, never a second live announcement.
            if (hasPreview) {
                preview.setAttribute('aria-live', 'off');
                preview.hidden = false;
            }
            if (progress) {
                progress.setAttribute('aria-hidden', 'true');
                progress.hidden = false;
            }
            if (counter) counter.setAttribute('aria-live', 'off');
            if (!experience) return;
            if (typeof window.IntersectionObserver !== 'function' || window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
                experience.classList.add('is-visible');
                return;
            }
            const observer = new IntersectionObserver(entries => {
                if (!entries.some(entry => entry.isIntersecting)) return;
                experience.classList.add('is-visible');
                observer.disconnect();
            }, { threshold: 0.05 });
            observer.observe(experience);
        }

        function describeField(field, id, enabled) {
            const description = new Set((field.getAttribute('aria-describedby') || '').split(/\s+/).filter(Boolean));
            if (enabled) description.add(id);
            else description.delete(id);
            if (description.size) field.setAttribute('aria-describedby', [...description].join(' '));
            else field.removeAttribute('aria-describedby');
        }

        function clearFieldError(field) {
            field.setCustomValidity('');
            field.removeAttribute('aria-invalid');
            describeField(field, feedback.id, false);
            if (invalidField === field) invalidField = null;
        }

        function clearMessage() {
            feedback.textContent = '';
            feedback.hidden = true;
            names.forEach(name => describeField(fields[name], feedback.id, false));
        }

        function updateContext() {
            if (!context) return;
            const selected = fields.subject.selectedOptions[0];
            const hasArea = Boolean(selected && selected.dataset.area);
            const message = hasArea ? 'Você escolheu ' + selected.textContent.trim() + '. Conte brevemente como podemos ajudar.' : '';
            if (context.textContent !== message) context.textContent = message;
            context.hidden = !hasArea;
            describeField(fields.subject, context.id, hasArea);
        }

        function showMessage(message, type) {
            feedback.hidden = false;
            feedback.className = 'form-message form-message-' + type;
            feedback.setAttribute('role', type === 'error' ? 'alert' : 'status');
            feedback.setAttribute('aria-live', type === 'error' ? 'assertive' : 'polite');
            feedback.textContent = message;
        }

        function rejectField(name, message) {
            const field = fields[name];
            invalidField = field;
            field.setCustomValidity(message);
            field.setAttribute('aria-invalid', 'true');
            describeField(field, feedback.id, true);
            showMessage(message, 'error');
            field.focus();
        }

        names.forEach(name => {
            const field = fields[name];
            function handleChange() {
                // Keep an unrelated field's error explained until that field is edited.
                const clearFeedback = !invalidField || invalidField === field;
                clearFieldError(field);
                // A previous prepared link becomes stale when any field changes.
                if (clearFeedback) clearMessage();
                if (name === 'subject') updateContext();
                form.classList.remove('is-prepared');
                updateExperience();
            }
            field.addEventListener('input', handleChange);
            field.addEventListener('change', handleChange);
        });

        // Accept only slugs supplied by the site's own options, never URL content as HTML.
        const requestedArea = new URLSearchParams(window.location.search).get('area');
        if (requestedArea) {
            const option = [...fields.subject.options].find(item => item.dataset.area === requestedArea);
            if (option) fields.subject.value = option.value;
        }
        updateContext();

        if (studio) {
            form.addEventListener('focusin', event => {
                if (names.includes(event.target.name)) studio.dataset.activeField = event.target.name;
                else delete studio.dataset.activeField;
            });
            form.addEventListener('focusout', event => {
                if (!form.contains(event.relatedTarget)) delete studio.dataset.activeField;
            });
        }

        form.addEventListener('reset', () => {
            names.forEach(name => clearFieldError(fields[name]));
            clearMessage();
            form.classList.remove('is-prepared');
            // The reset event runs before the browser restores each default value.
            window.setTimeout(() => {
                updateContext();
                updateExperience();
            }, 0);
        });

        form.addEventListener('submit', event => {
            event.preventDefault();
            if (opening) return;
            names.forEach(name => clearFieldError(fields[name]));
            clearMessage();
            form.classList.remove('is-prepared');
            updateExperience();
            const data = Object.fromEntries(names.map(name => [name, String(fields[name].value || '').trim()]));
            const requiredMessages = {
                name: 'Informe seu nome para preparar a conversa.',
                phone: 'Informe seu WhatsApp com o código de área (DDD).',
                subject: 'Informe o assunto do atendimento.',
                message: 'Escreva um breve resumo do que você precisa.'
            };
            for (const name of names) {
                if (!data[name]) {
                    rejectField(name, requiredMessages[name]);
                    return;
                }
            }
            if (!plausiblePhone(data.phone)) {
                rejectField('phone', 'Confira o WhatsApp: inclua o DDD e use de 10 a 15 dígitos.');
                return;
            }
            for (const name of names) {
                const limit = fields[name].maxLength;
                if (limit > 0 && data[name].length > limit) {
                    rejectField(name, 'Reduza este campo para até ' + limit + ' caracteres.');
                    return;
                }
            }
            for (const name of names) {
                if (!fields[name].validity.valid) {
                    rejectField(name, fields[name].validationMessage || 'Confira este campo antes de continuar.');
                    return;
                }
            }

            const officeNumber = form.dataset.whatsapp || '';
            if (!/^\d{10,15}$/.test(officeNumber)) {
                showMessage('Não foi possível preparar o link do WhatsApp. Entre em contato pelos canais de telefone ou e-mail desta página.', 'error');
                feedback.setAttribute('tabindex', '-1');
                feedback.focus();
                return;
            }
            const text = [
                'Olá, gostaria de atendimento jurídico.',
                '',
                'Nome: ' + data.name,
                'WhatsApp: ' + data.phone,
                'Assunto: ' + data.subject,
                'Mensagem: ' + data.message
            ].join('\n');
            const url = 'https://wa.me/' + officeNumber + '?text=' + encodeURIComponent(text);
            opening = true;
            form.classList.add('is-prepared');
            if (submit) {
                submit.disabled = true;
                submit.textContent = 'Conversa preparada';
            }

            showMessage('Sua mensagem está pronta. Revise e envie no WhatsApp. Se a conversa não abrir, ', 'success');
            const fallback = document.createElement('a');
            fallback.href = url;
            fallback.target = '_blank';
            fallback.rel = 'noopener noreferrer';
            fallback.textContent = 'continue por este link';
            feedback.append(fallback, '.');

            // noopener can return null even on success. Never open a second tab automatically.
            try {
                window.open(url, '_blank', 'noopener,noreferrer');
            } catch {
                // The visible link also works when a browser extension blocks window.open.
            } finally {
                window.setTimeout(() => {
                    opening = false;
                    if (submit) {
                        submit.disabled = false;
                        submit.replaceChildren(...submitContent.map(node => node.cloneNode(true)));
                    }
                }, 1200);
            }
        });

        updateExperience();
        revealExperience();
        // Enable submission only after the WhatsApp handler is ready.
        form.noValidate = true;
        form.dataset.contactReady = 'true';
        if (submit) submit.disabled = false;
    }

    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initializeContactForm, { once: true });
    else initializeContactForm();
})();
