use std::net::UdpSocket;

use artnet_protocol::ArtCommand;
use kiss3d::{camera::ArcBall, light::Light, scene::SceneNode, window::Window};
use nalgebra::{Point3, Translation3, UnitQuaternion, Vector3};
use rand::random;

struct Face {
    switch: bool,
    flow: u8,
    fire_cone: SceneNode,
}
impl Face {
    pub fn new(
        vertex_indices: [usize; 4],
        vertices: &[Vector3<f32>; 32],
        window: &mut Window,
        quaternion_to_rotate_5_pyramid_to_top: &UnitQuaternion<f32>,
    ) -> Self {
        let center_vector =
            // Average the vertex vectors to create the vector to the center of the face
            (vertices[vertex_indices[0]]
                + vertices[vertex_indices[1]]
                + vertices[vertex_indices[2]]
                + vertices[vertex_indices[3]])
                / 4.;
        let mut quad = window.add_quad_with_vertices(
            vertex_indices
                .iter()
                .map(|vertex_index| Point3::<f32>::from(vertices[*vertex_index]))
                .collect::<Vec<_>>()
                .as_slice(),
            2,
            2,
        );
        quad.append_rotation(quaternion_to_rotate_5_pyramid_to_top);
        quad.set_color(random(), random(), random());

        let mut fire_cone = window.add_cone(0.5, 2.);
        fire_cone.append_rotation(
            &UnitQuaternion::rotation_between(&(-Vector3::y()), &center_vector).unwrap_or_else(
                || UnitQuaternion::from_axis_angle(&Vector3::x_axis(), std::f32::consts::PI),
            ),
        );
        fire_cone.set_points_size(10.0);
        fire_cone.set_lines_width(1.0);
        fire_cone.set_surface_rendering_activation(false);
        fire_cone.append_translation(&Translation3::from(center_vector * 1.5));
        fire_cone.append_rotation(quaternion_to_rotate_5_pyramid_to_top);
        fire_cone.set_color(1., 0.8, 0.2);

        Self {
            switch: false,
            flow: 255,
            fire_cone,
        }
    }
}

fn main() {
    let socket = setup_socket();
    let c0: f32 = 5f32.sqrt() / 4.;
    let c1: f32 = (5. + 5f32.sqrt()) / 8.;
    let c2: f32 = (5. + 3. * 5f32.sqrt()) / 8.;
    let z: f32 = 0.;

    let vertices: [Vector3<f32>; 32] = [
        [c1, z, c2].into(),
        [c1, z, -c2].into(),
        [-c1, z, c2].into(),
        [-c1, z, -c2].into(),
        [c2, c1, z].into(),
        [c2, -c1, z].into(),
        [-c2, c1, z].into(),
        [-c2, -c1, z].into(),
        [z, c2, c1].into(),
        [z, c2, -c1].into(),
        [z, -c2, c1].into(),
        [z, -c2, -c1].into(),
        [z, c0, c2].into(),
        [z, c0, -c2].into(),
        [z, -c0, c2].into(),
        [z, -c0, -c2].into(),
        [c2, z, c0].into(),
        [c2, z, -c0].into(),
        [-c2, z, c0].into(),
        [-c2, z, -c0].into(),
        [c0, c2, z].into(),
        [c0, -c2, z].into(),
        [-c0, c2, z].into(),
        [-c0, -c2, z].into(),
        [c1, c1, c1].into(),
        [c1, c1, -c1].into(),
        [c1, -c1, c1].into(),
        [c1, -c1, -c1].into(),
        [-c1, c1, c1].into(),
        [-c1, c1, -c1].into(),
        [-c1, -c1, c1].into(),
        [-c1, -c1, -c1].into(),
    ];

    let mut window = Window::new("Light Curve Simulator");
    let quaternion_to_rotate_5_pyramid_to_top =
        UnitQuaternion::rotation_between(&vertices[8], &Vector3::y()).unwrap();
    let face_vertex_indices: [[usize; 4]; 30] = [
        [23, 10, 11, 21],
        [27, 11, 5, 21],
        [15, 11, 1, 27],
        [31, 11, 3, 15],
        [31, 7, 11, 23],
        [21, 10, 5, 26],
        [17, 1, 5, 27],
        [13, 3, 1, 15],
        [19, 7, 3, 31],
        [30, 10, 7, 23],
        [14, 0, 10, 26],
        [26, 0, 5, 16],
        [16, 4, 5, 17],
        [25, 1, 4, 17],
        [13, 1, 9, 25],
        [29, 3, 9, 13],
        [19, 3, 6, 29],
        [18, 7, 6, 19],
        [18, 2, 7, 30],
        [30, 2, 10, 14],
        [12, 0, 2, 14],
        [24, 4, 0, 16],
        [20, 9, 4, 25],
        [29, 9, 6, 22],
        [28, 2, 6, 18],
        [12, 8, 0, 24],
        [20, 4, 8, 24],
        [22, 9, 8, 20],
        [22, 8, 6, 28],
        [28, 8, 2, 12],
    ];
    // Original order with numbered sides:
    // [12, 0, 2, 14], 21
    // [14, 0, 10, 26], 11
    // [26, 0, 5, 16], 12
    // [13, 1, 9, 25], 15
    // [25, 1, 4, 17], 14
    // [17, 1, 5, 27], 07
    // [28, 2, 6, 18], 25
    // [18, 2, 7, 30], 19
    // [30, 2, 10, 14], 20
    // [19, 3, 6, 29], 17
    // [29, 3, 9, 13], 16
    // [13, 3, 1, 15], 08
    // [20, 4, 8, 24], 27
    // [24, 4, 0, 16], 22
    // [16, 4, 5, 17], 13
    // [18, 7, 6, 19], 18
    // [19, 7, 3, 31], 09
    // [31, 7, 11, 23], 05
    // [22, 8, 6, 28], 29
    // [28, 8, 2, 12], 30
    // [12, 8, 0, 24], 26
    // [29, 9, 6, 22], 24
    // [22, 9, 8, 20], 28
    // [20, 9, 4, 25], 23
    // [30, 10, 7, 23], 10
    // [23, 10, 11, 21], 01
    // [21, 10, 5, 26], 06
    // [31, 11, 3, 15], 04
    // [15, 11, 1, 27], 03
    // [27, 11, 5, 21], 02

    let mut faces: [Face; 30] = face_vertex_indices.map(|indices| {
        Face::new(
            indices,
            &vertices,
            &mut window,
            &quaternion_to_rotate_5_pyramid_to_top,
        )
    });

    window.set_light(Light::StickToCamera);

    let mut arc_ball_camera = ArcBall::new(Point3::new(0.0f32, 0., 10.), Point3::origin());

    while !window.should_close() {
        window.render_with_camera(&mut arc_ball_camera);
        receive_artnet(&mut faces, &socket);
    }
}

fn setup_socket() -> UdpSocket {
    let udp_socket = match UdpSocket::bind("0.0.0.0:6454") {
        Ok(socket) => socket,
        Err(e) => {
            println!("Error binding: {:?}", e);
            panic!();
        }
    };
    udp_socket.set_nonblocking(true).unwrap();
    udp_socket
}

fn receive_artnet(faces: &mut [Face; 30], socket: &UdpSocket) {
    let mut response_buf = [0u8; 65507];
    let Ok((response_length, sender_address)) = socket.recv_from(&mut response_buf) else {
        // Received nothing
        return;
    };

    match ArtCommand::from_buffer(&response_buf[..response_length]) {
        Ok(ArtCommand::Output(output)) => {
            let data = output.data.as_ref();
            data.chunks_exact(2)
                .zip(faces.iter_mut())
                .for_each(|(bytes, face)| {
                    face.switch = bytes[0] > 0;
                    face.flow = bytes[1];
                    let flow_proportion = face.flow as f32 / 255.;
                    if face.switch {
                        face.fire_cone.set_local_scale(1., flow_proportion * 2., 1.);
                    } else {
                        face.fire_cone.set_local_scale(0., 0., 0.);
                    }
                });
        }
        Err(e) => {
            println!(
                "Received bytes that aren't a valid artnet command from {:?}. Error: {:?}",
                sender_address, e
            );
        }
        _ => {
            // E.g. this will happen when the device receives its own poll message that was broadcast on the network.
            println!("Received other artnet from {:?}", sender_address);
        }
    }
}
